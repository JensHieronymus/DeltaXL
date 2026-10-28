"""The main window. It only collects settings and shows results; the work is done in deltaxl.theory."""

import math
from dataclasses import dataclass
from types import SimpleNamespace

from PySide6.QtCore import QSortFilterProxyModel, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QBrush, QFontMetricsF, QTextLayout
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QGridLayout, QInputDialog,
    QGroupBox, QHBoxLayout, QLabel, QLayout, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QRadioButton, QButtonGroup, QSpinBox, QStackedWidget, QTableView,
    QTabWidget, QVBoxLayout, QWidget, QScrollArea, QSplitter, QTableWidget, QTableWidgetItem, QComboBox, QHeaderView
)

from deltaxl import __version__
from deltaxl.gui.models import TableModel
from deltaxl.gui.enzymes import DEFAULT_ENZYME, ENZYMES
from deltaxl.gui.modifications import (
    CARBAMIDOMETHYL, DEFAULT_FIXED, SUGGESTIONS,
)
from deltaxl.io.fasta import read_fasta
from deltaxl.io.writers import (
    PEPTIDE_COLUMNS, SPECIES_COLUMNS, peptide_row, species_row,
    write_peptides_csv, write_species_csv,
)
from deltaxl.theory.pipeline import KINDS, Options, digest_fasta, iter_species

from pathlib import Path


MAX_SPECIES_ROWS = 50_000  # rows shown in the table; the CSV export always contains all of them


@dataclass
class Result:
    peptides: list
    lengths: dict
    species_rows: list
    species_total: int


class Worker(QThread):
    """Runs digestion and crosslink generation away from the interface thread."""

    done = Signal(object)
    failed = Signal(str)

    def __init__(self, path, options, parent=None):
        super().__init__(parent)
        self.path = path
        self.options = options

    def run(self):
        try:
            peptides, lengths = digest_fasta(self.path, self.options)
            rows, total = [], 0
            for sp in iter_species(peptides, lengths, self.options):
                total += 1
                if len(rows) < MAX_SPECIES_ROWS:
                    rows.append(species_row(sp))
            self.done.emit(Result(peptides, lengths, rows, total))
        except (OSError, ValueError) as error:
            self.failed.emit(str(error))


def _make_table(model):
    proxy = QSortFilterProxyModel()
    proxy.setSourceModel(model)
    proxy.setSortRole(Qt.UserRole)
    view = QTableView()
    view.setModel(proxy)
    view.setSortingEnabled(True)
    view.setAlternatingRowColors(True)
    view.setSelectionBehavior(QAbstractItemView.SelectRows)
    view.setEditTriggers(QAbstractItemView.NoEditTriggers)
    view.verticalHeader().setVisible(False)
    view.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    view.horizontalHeader().setDefaultSectionSize(135)
    view.horizontalHeader().setStretchLastSection(True)
    return view, proxy


class AutoHeightEdit(QPlainTextEdit):
    """A text field that is exactly as tall as its text and grows with it.

    After max_lines lines it stops growing and gets its own scroll bar. Below that it never scrolls.
    """

    def __init__(self, text="", max_lines=10):
        super().__init__(text)
        self.max_lines = max_lines
        self.textChanged.connect(self._fit_later)   # typing, pasting, setPlainText, append
        self._fit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_later()                            # a new width changes how lines wrap

    def wheelEvent(self, event):
        if self.verticalScrollBarPolicy() == Qt.ScrollBarAlwaysOff:
            event.ignore()                           # nothing to scroll here: let the page scroll
        else:
            super().wheelEvent(event)

    def _fit_later(self):
        QTimer.singleShot(0, self._fit)              # wait until the text has been laid out

    def _count_lines(self):
        """Count the lines the text takes at the current width, wrapped lines included.

        Qt only lays out the part of a long text it needs, so its own line count can be a few
        lines short; counting them here gives the exact number."""
        doc = self.document()
        width = self.viewport().width() - 2 * doc.documentMargin()
        if width <= 0:
            return int(doc.size().height())
        total = 0
        block = doc.begin()
        while block.isValid():
            layout = QTextLayout(block.text(), self.font())
            layout.setTextOption(doc.defaultTextOption())
            layout.beginLayout()
            count = 0
            while True:
                line = layout.createLine()
                if not line.isValid():
                    break
                line.setLineWidth(width)
                count += 1
            layout.endLayout()
            total += max(count, 1)
            block = block.next()
        return total

    def _fit(self):
        total = self._count_lines()
        lines = min(max(total, 1), self.max_lines)
        pad = 2 * self.document().documentMargin() + 2 * self.frameWidth()
        line_height = QFontMetricsF(self.font()).lineSpacing()   # a fractional number of pixels
        height = math.ceil(lines * line_height + pad) + 2        # +2 px so Qt sees no hidden extra line
        if height != self.height():
            self.setFixedHeight(height)
        too_long = total > self.max_lines
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded if too_long else Qt.ScrollBarAlwaysOff)
        if not too_long:
            # while typing, Qt scrolls the text up a line before the box has grown; scroll back
            self.verticalScrollBar().setValue(0)


class SequenceBox(QGroupBox):
    """One protein: a title, a text field and its own buttons. It remembers its own protein."""

    removed = Signal(object)  # tells the window "remove me"
    changed = Signal()        # the header or sequence was edited
    duplicated = Signal(object)  # tells the window "make a copy of me"

    def __init__(self, protein, filename):
        super().__init__(f"{filename}")
        self.protein = protein      # as loaded from the file
        self.filename = filename
        self.header = protein.header      # what the text field currently says
        self.sequence = protein.sequence

        grid = QGridLayout(self)
        self.text = AutoHeightEdit(">" + protein.header + "\n" + protein.sequence)
        self._edited = QTimer(self)                 # wait until typing pauses, then tell the window
        self._edited.setSingleShot(True)
        self._edited.setInterval(300)
        self._edited.timeout.connect(self._read_text)
        self.text.textChanged.connect(self._edited.start)
        grid.addWidget(self.text, 0, 0, 1, 3)
        copy = QPushButton("Copy sequence")
        copy.clicked.connect(self.copy_sequence)  # self is this box
        duplicate = QPushButton("Duplicate")
        duplicate.clicked.connect(lambda: self.duplicated.emit(self))
        remove = QPushButton("Remove")
        remove.clicked.connect(lambda: self.removed.emit(self))
        grid.addWidget(copy, 1, 0)
        grid.addWidget(duplicate, 1, 1)
        grid.addWidget(remove, 1, 2)

    def _read_text(self):
        """Take the header (first line starting with >) and the sequence from the text field."""
        lines = self.text.toPlainText().splitlines()
        header = ""
        if lines and lines[0].startswith(">"):
            header = lines.pop(0)[1:].strip()
        sequence = "".join("".join(lines).split())
        if (header, sequence) != (self.header, self.sequence):
            self.header, self.sequence = header, sequence
            self.changed.emit()

    def copy_sequence(self):
        QApplication.clipboard().setText(self.sequence)

class AssignmentTable(QTableWidget):
    """One row per unique header + sequence: which protein it belongs to, its header, and the copies.

    The protein name defaults to the file name without extension; pick another from the dropdown,
    or add one with the button (it is then offered in every dropdown). Copies can be edited."""

    def __init__(self):
        super().__init__(0, 3)
        self.setHorizontalHeaderLabels(["Protein assignment", "Sequence header", "Copies"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.extra_names = []   # names added with the button
        # the table never scrolls itself: it is as tall as its rows, and the page scrolls instead
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().setVisible(False)

    def refresh(self, boxes):
        # what the user already set, kept per row. A row is found again by its (header, sequence),
        # or, if one of those was just edited, by sharing a sequence box with the old row.
        old = []   # (key, box ids, chosen name or None, copies or None)
        for r in range(self.rowCount()):
            item = self.item(r, 1)
            combo, spin = self.cellWidget(r, 0), self.cellWidget(r, 2)
            old.append((item.data(Qt.UserRole), set(item.data(Qt.UserRole + 1)),
                        combo.currentText() if combo.property("user_set") else None,
                        spin.value() if spin.property("user_set") else None))

        groups = {}   # (header, sequence) -> boxes that hold exactly this
        for b in boxes:
            groups.setdefault((b.header, b.sequence), []).append(b)

        def remembered(key, owners):
            ids = {id(o) for o in owners}
            for old_key, old_ids, name, copies in old:
                if old_key == key:
                    return name, copies
            for old_key, old_ids, name, copies in old:
                if old_ids & ids:   # same box(es) edited: keep the name; keep Copies if nothing split
                    return name, (copies if old_ids == ids else None)
            return None, None

        rows = [(key, owners) + remembered(key, owners) for key, owners in groups.items()]

        names = []
        for name in ([Path(b.filename).stem for b in boxes] + self.extra_names
                     + [r[2] for r in rows if r[2]]):
            if name not in names:
                names.append(name)

        # a number after the header when different sequences share it: heavy, heavy (2), ...
        labels, seen = [], {}
        for (header, _), *_ in rows:
            label = header or "(no header)"
            seen[label] = seen.get(label, 0) + 1
            labels.append(label if seen[label] == 1 else f"{label} ({seen[label]})")

        self.setRowCount(len(rows))
        for row, (key, owners, name, copies) in enumerate(rows):
            combo = QComboBox()
            combo.addItems(names)
            combo.setCurrentText(name or Path(owners[0].filename).stem)
            combo.setProperty("user_set", name is not None)
            combo.activated.connect(lambda _, c=combo: c.setProperty("user_set", True))
            self.setCellWidget(row, 0, combo)

            header = QTableWidgetItem(labels[row])
            header.setData(Qt.UserRole, key)                  # (header, sequence)
            header.setData(Qt.UserRole + 1, [id(o) for o in owners])
            header.setFlags(header.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 1, header)

            spin = QSpinBox()                                 # editable, starts at the counted copies
            spin.setRange(1, 999)
            spin.setValue(copies if copies is not None else len(owners))
            spin.setProperty("user_set", copies is not None)
            spin.valueChanged.connect(lambda _, w=spin: w.setProperty("user_set", True))
            self.setCellWidget(row, 2, spin)
        self._fit_height()

    def _fit_height(self):
        """Exactly tall enough for the header and the rows: short with one row, longer with more."""
        self.resizeRowsToContents()
        rows = sum(self.rowHeight(r) for r in range(self.rowCount()))
        self.setFixedHeight(self.horizontalHeader().height() + rows + 2 * self.frameWidth())

    def add_name(self, name):
        if name and name not in self.extra_names:
            self.extra_names.append(name)

    def assignments(self):
        """Returns {(header, sequence): protein name}"""
        return {self.item(r, 1).data(Qt.UserRole): self.cellWidget(r, 0).currentText()
                for r in range(self.rowCount())}


class ModificationList(QWidget):
    """A list of modifications: residue, the new symbol, and the mass change.

    Add one by hand, or double-click a suggestion (the suggestions live in modifications.py)."""

    def __init__(self, suggestions=()):
        super().__init__()
        # text a little bigger than the rest of the window
        self.setObjectName("modList")
        size = QApplication.font().pointSizeF()
        if size > 0:
            self.setStyleSheet(
                f"#modList QTableWidget, #modList QHeaderView, #modList QListWidget, "
                f"#modList QLineEdit, #modList QDoubleSpinBox, #modList QPushButton, "
                f"#modList QLabel {{ font-size: {size + 1:g}pt; }}")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Residue", "Modification Notation", "Total Mass (Da)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setMinimumHeight(110)

        self.residue = QLineEdit()
        self.residue.setPlaceholderText("M")
        self.residue.setMaxLength(1)
        self.residue.setMaximumWidth(50)
        self.symbol = QLineEdit()
        self.symbol.setPlaceholderText("Mox")
        self.mass = QDoubleSpinBox()
        self.mass.setRange(-1000, 1000)
        self.mass.setDecimals(4)
        self.symbol.setMaximumWidth(90)          # room for a short notation like Mox, no more
        self.mass.setMaximumWidth(100)
        add = QPushButton("Add")
        add.clicked.connect(self.add)
        remove = QPushButton("Remove selected")
        remove.clicked.connect(self.remove_selected)

        self.suggestions = QListWidget()
        self.suggestions.setMinimumHeight(110)
        for mod in suggestions:
            item = QListWidgetItem(mod.label())
            item.setData(Qt.UserRole, mod)
            item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)   # the tick is only an indicator
            item.setCheckState(Qt.Unchecked)
            self.suggestions.addItem(item)
        self.suggestions.itemDoubleClicked.connect(self._add_suggestion)

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(self.table, 0, 0, 1, 5)
        # one row: the fields on the left (the Da label sits right of the mass box), the buttons right
        fields = QHBoxLayout()
        fields.addWidget(self.residue)
        fields.addWidget(self.symbol)
        fields.addWidget(self.mass)
        fields.addWidget(QLabel("Da"))
        fields.addStretch(1)
        fields.addWidget(add)
        fields.addWidget(remove)
        grid.addLayout(fields, 1, 0, 1, 5)
        grid.addWidget(QLabel("Suggestions (double-click to add or remove)"), 2, 0, 1, 5)
        grid.addWidget(self.suggestions, 3, 0, 1, 5)

    def add(self):
        residue = self.residue.text().strip().upper()
        symbol = self.symbol.text().strip()
        if not residue.isalpha() or not symbol:
            QMessageBox.information(self, "DeltaXL", "Give a residue letter and a new symbol.")
            return
        if self.add_mod(residue, symbol, self.mass.value()):
            self.residue.clear()
            self.symbol.clear()
            self.mass.setValue(0)

    def _add_suggestion(self, item):
        """Double-click: add the modification, or remove it again if it is already ticked."""
        mod = item.data(Qt.UserRole)
        for row in range(self.table.rowCount()):
            if self.table.item(row, 1).text() == mod.symbol:
                self.table.removeRow(row)
                self._update_ticks()
                return
        self.add_mod(mod.residue, mod.symbol, mod.mass)

    def add_mod(self, residue, symbol, mass):
        """Add a row. Returns False (with a message) if the symbol is already in the list."""
        if symbol in [m[1] for m in self.mods()]:
            QMessageBox.information(self, "DeltaXL", f"The symbol {symbol} is already in the list.")
            return False
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, text in enumerate((residue, symbol, f"{mass:.4f}")):
            self.table.setItem(row, col, QTableWidgetItem(text))
        self._update_ticks()
        return True

    def _update_ticks(self):
        """Tick and highlight the suggestions that are in the table."""
        used = {m[1] for m in self.mods()}
        shade = self.palette().highlight().color()
        shade.setAlpha(90)                       # the system highlight colour, softened
        for i in range(self.suggestions.count()):
            item = self.suggestions.item(i)
            ticked = item.data(Qt.UserRole).symbol in used
            item.setCheckState(Qt.Checked if ticked else Qt.Unchecked)
            item.setBackground(shade if ticked else QBrush())

    def remove_selected(self):
        for row in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(row)
        self._update_ticks()

    def mods(self):
        """Returns [(residue, symbol, mass change), ...]"""
        return [(self.table.item(r, 0).text(), self.table.item(r, 1).text(),
                 float(self.table.item(r, 2).text())) for r in range(self.table.rowCount())]


class EnzymePanel(QGroupBox):
    """One enzyme: a preset (or Custom), its cleavage rule and its missed cleavages."""

    removed = Signal(object)   # tells the window "remove me"

    def __init__(self, enzyme=DEFAULT_ENZYME):
        super().__init__()
        self.setFixedWidth(250)
        self.enzyme_combo = QComboBox()
        self.enzyme_combo.addItems([e.name for e in ENZYMES] + ["Custom"])
        self.cut_side = QComboBox()
        self.cut_side.addItems(["after", "before"])
        self.cut_residues = QLineEdit()
        self.cut_residues.setPlaceholderText("KR")
        self.cut_exceptions = QLineEdit()
        self.cut_exceptions.setPlaceholderText("none")
        self.exception_label = QLabel()
        self.missed = QSpinBox()
        self.missed.setRange(0, 6)
        self.missed.setValue(2)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(lambda: self.removed.emit(self))

        grid = QGridLayout(self)
        grid.setColumnStretch(1, 1)
        grid.addWidget(QLabel("Enzyme"), 0, 0)
        grid.addWidget(self.enzyme_combo, 0, 1)
        grid.addWidget(QLabel("Cuts"), 1, 0)
        grid.addWidget(self.cut_side, 1, 1)
        grid.addWidget(QLabel("these residues"), 2, 0)
        grid.addWidget(self.cut_residues, 2, 1)
        grid.addWidget(self.exception_label, 3, 0)
        grid.addWidget(self.cut_exceptions, 3, 1)
        grid.addWidget(QLabel("Missed cleavages"), 4, 0)
        grid.addWidget(self.missed, 4, 1)
        grid.addWidget(self.remove_button, 5, 0, 1, 2)

        # a preset fills in the rule; changing the rule by hand switches the enzyme to "Custom"
        self.enzyme_combo.activated.connect(self._pick_enzyme)
        self.cut_side.activated.connect(self._rule_edited)
        self.cut_residues.textEdited.connect(self._rule_edited)
        self.cut_exceptions.textEdited.connect(self._rule_edited)
        self.show_enzyme(enzyme)

    def show_enzyme(self, enzyme):
        self.enzyme_combo.setCurrentText(enzyme.name)
        self.cut_side.setCurrentText(enzyme.side)
        self.cut_residues.setText(enzyme.residues)
        self.cut_exceptions.setText(enzyme.exceptions)
        self._update_exception_label()

    def _pick_enzyme(self):
        for enzyme in ENZYMES:
            if enzyme.name == self.enzyme_combo.currentText():
                self.show_enzyme(enzyme)

    def _rule_edited(self):
        self.enzyme_combo.setCurrentText("Custom")
        self._update_exception_label()

    def _update_exception_label(self):
        self.exception_label.setText(
            "unless next is" if self.cut_side.currentText() == "after" else "unless previous is")

    def rule(self):
        """Returns (name, side, residues, exceptions, missed cleavages)"""
        return (self.enzyme_combo.currentText(), self.cut_side.currentText(),
                self.cut_residues.text().strip().upper(), self.cut_exceptions.text().strip().upper(),
                self.missed.value())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeltaXL")
        self.resize(1100, 680)
        self.result = None
        self.sequence_boxes = []  # one SequenceBox per protein
        self.worker = None
        self._last_options = None
        self._build_ui()
        self._build_menu()
        self.statusBar().showMessage("Ready...")

    # ---- layout -------------------------------------------------------------------------
    # The window is a workflow: a list of steps on the left, the page of the chosen step on the
    # right. To add a step, add its name to STEPS and add a page in _build_ui.
    STEPS = ("1.  Protein Input",
             "2.  Digestion and Modifications",
             "3.  Crosslinker",
             "4.  Results")

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        layout = QHBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 6)

        # left: list of steps, plus Run and the progress bar
        side = QVBoxLayout()
        side.setContentsMargins(0, 0, 0, 0)
        header = QLabel("Workflow")
        header.setObjectName("taskHeader")
        side.addWidget(header)
        self.step_list = QListWidget()
        self.step_list.setObjectName("stepList")
        self.step_list.addItems(self.STEPS)
        self.step_list.setFocusPolicy(Qt.NoFocus)
        self.step_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.step_list.setFixedHeight(len(self.STEPS) * 48 + 4)
        side.addWidget(self.step_list)
        side.addSpacing(8)
        self.run_button = QPushButton("Run analysis")
        self.run_button.setObjectName("runButton")
        self.run_button.clicked.connect(self.run)
        side.addWidget(self.run_button)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        side.addWidget(self.progress)
        side.addStretch(1)
        side_widget = QWidget()
        side_widget.setObjectName("taskPane")
        side_widget.setAttribute(Qt.WA_StyledBackground, True)
        side_widget.setLayout(side)
        side_widget.setFixedWidth(200)
        layout.addWidget(side_widget)

        # right: one page per step
        self.pages = QStackedWidget()
        self.pages.addWidget(self._page(
            0, "Protein Input", "Choose the protein sequences to digest.", self._input_box(),
            grow=True))
        self.pages.addWidget(self._page(
            1, "Digestion and Modifications",
            "Set the modifications and how the enzyme cuts the proteins in silico.", self._digest_box()))
        self.pages.addWidget(self._page(
            2, "Crosslinker", "Choose which DSBU species to generate. Then press Run analysis.",
            self._species_box()))
        self.pages.addWidget(self._results_page())
        layout.addWidget(self.pages, 1)

        self.step_list.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.step_list.setCurrentRow(0)
        self.setCentralWidget(central)

    def _page(self, index, title, hint, content, grow=False):
        """A settings page: title, short hint, the settings, and Back / Next buttons."""
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(16, 8, 8, 8)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        note = QLabel(hint)
        note.setObjectName("pageHint")
        note.setWordWrap(True)
        
        col.addWidget(heading)
        col.addWidget(note)
        col.addSpacing(6)
        col.addWidget(content, 1 if grow else 0)
        if not grow:
            col.addStretch(1)
        nav = QHBoxLayout()
        nav.addStretch(1)
        if index > 0:
            back = QPushButton("Back")
            back.clicked.connect(lambda: self.step_list.setCurrentRow(index - 1))
            nav.addWidget(back)
        nxt = QPushButton("Next")
        nxt.clicked.connect(lambda: self.step_list.setCurrentRow(index + 1))
        nav.addWidget(nxt)
        col.addLayout(nav)
        return page

    def _results_page(self):
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(16, 8, 8, 8)
        heading = QLabel("Results")
        heading.setObjectName("pageTitle")
        self.summary = QLabel("Press Run analysis to see results here.")
        self.summary.setObjectName("pageHint")
        
        col.addWidget(heading)
        col.addWidget(self.summary)
        self.peptide_model = TableModel(PEPTIDE_COLUMNS)
        self.species_model = TableModel(SPECIES_COLUMNS)
        peptide_view, _ = _make_table(self.peptide_model)
        species_view, _ = _make_table(self.species_model)
        self.tabs = QTabWidget()
        self.tabs.addTab(peptide_view, "Peptides")
        self.tabs.addTab(species_view, "Crosslinked species")
        col.addWidget(self.tabs, 1)
        nav = QHBoxLayout()
        nav.addStretch(1)
        back = QPushButton("Back to settings")
        back.clicked.connect(lambda: self.step_list.setCurrentRow(2))
        nav.addWidget(back)
        col.addLayout(nav)
        return page


    def _input_box(self):
        # the box that stays at the top of the page
        input_box = QGroupBox("Protein Sequence(s)")
        row = QHBoxLayout(input_box)
        self.fasta_edit = QLineEdit()
        self.fasta_edit.setPlaceholderText("FASTA file")
        browse_fasta = QPushButton("Open...")
        browse_fasta.clicked.connect(self.open_fasta)
        row.addWidget(self.fasta_edit, 1)
        row.addWidget(browse_fasta)

        self.settings_box = QGroupBox("Settings")
        settings_grid = QGridLayout(self.settings_box)
        self.settings_table = AssignmentTable()
        settings_grid.addWidget(self.settings_table, 0, 0)
        add_name = QPushButton("Add protein assignment name")
        add_name.clicked.connect(self.add_assignment_name)
        settings_grid.addWidget(add_name, 1, 0, alignment=Qt.AlignRight)

        # the settings scroll like the sequence boxes do; the stretch under the box keeps it only
        # as tall as its content, at the top
        settings_container = QWidget()
        settings_column = QVBoxLayout(settings_container)
        settings_column.setContentsMargins(0, 0, 0, 0)
        settings_column.addWidget(self.settings_box)
        settings_column.addStretch(1)
        settings_column.setSizeConstraint(QLayout.SetMinimumSize)
        self.settings_scroll = QScrollArea()
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setFrameShape(QFrame.NoFrame)
        self.settings_scroll.setWidget(settings_container)
        self.settings_scroll.hide()   # nothing to show until a protein is loaded


        # a column for the sequence boxes that are added later; the stretch at the end keeps
        # the boxes at the top of the scroll area
        container = QWidget()
        self.input_column = QVBoxLayout(container)
        self.input_column.setContentsMargins(0, 0, 0, 0)
        self.input_column.addStretch(1)
        self.input_column.setSizeConstraint(QLayout.SetMinimumSize)  # lets the scroll area scroll

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(container)

        # the whole Input page: fixed box on top, under it two columns:
        # the sequence boxes (scrolling) on the left and the settings on the right
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 0, 0, 0)
        col.addWidget(input_box)
        columns = QSplitter(Qt.Horizontal)          # drag the divider to resize the two columns
        columns.setChildrenCollapsible(False)
        columns.setHandleWidth(8)
        columns.addWidget(scroll)
        columns.addWidget(self.settings_scroll)
        columns.setStretchFactor(0, 1)
        columns.setStretchFactor(1, 1)
        columns.setSizes([500, 500])                # start with equal widths
        col.addWidget(columns, 1)
        return page


    def add_protein_box(self, protein, filename, after=None):
        """Make a SequenceBox for a protein and put it in the scroll area, above the stretch.

        With after=box, the new box goes right under that box instead of at the end."""
        box = SequenceBox(protein, filename)
        box.removed.connect(self.remove_box)
        box.duplicated.connect(self.duplicate_box)
        box.changed.connect(self._refresh_settings)   # an edited header or sequence updates Settings
        if after is None:
            self.sequence_boxes.append(box)
            self.input_column.insertWidget(self.input_column.count() - 1, box)
        else:
            index = self.sequence_boxes.index(after) + 1
            self.sequence_boxes.insert(index, box)
            self.input_column.insertWidget(index, box)
        self._refresh_settings()

    def duplicate_box(self, box):
        """A copy of a box, as it is now (with any edits), right under it."""
        copy = SimpleNamespace(header=box.header, sequence=box.sequence)
        self.add_protein_box(copy, box.filename, after=box)

    def remove_box(self, box):
        self.sequence_boxes.remove(box)
        box.deleteLater()
        self._refresh_settings()

    def add_assignment_name(self):
        name, ok = QInputDialog.getText(self, "DeltaXL", "Protein assignment name:")
        if ok and name.strip():
            self.settings_table.add_name(name.strip())
            self._refresh_settings()

    def _refresh_settings(self):
        self.settings_table.refresh(self.sequence_boxes)
        self.settings_scroll.setVisible(bool(self.sequence_boxes))

    def set_locked(self):
        for box in self.sequence_boxes:
            box.text.setReadOnly(locked)

    def _digest_box(self):
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 0, 0, 0)

        box = QGroupBox("Digestion Enzyme")
        row = QHBoxLayout(box)

        # left, fixed: settings that apply to the peptides whatever the enzyme. Each limit can be
        # given in amino acids (AA) or in Da, and each has a check box that turns it on or off
        general = QVBoxLayout()
        (self.min_aa_check, self.min_len,
         self.min_da_check, self.min_da) = self._limit_rows(general, "Min. Peptide", 4, True, 600, False)
        general.addSpacing(8)
        (self.max_aa_check, self.max_len,
         self.max_da_check, self.max_da) = self._limit_rows(general, "Max. Peptide", 40, False, 6000, False)

        # only shown once there are two or more enzymes
        self.combine_box = QWidget()
        combine_col = QVBoxLayout(self.combine_box)
        combine_col.setContentsMargins(0, 8, 0, 0)
        combine_col.addWidget(QLabel("Apply the enzymes"))
        self.parallel_radio = QRadioButton("in parallel")
        self.parallel_radio.setToolTip("Each enzyme digests the protein on its own; the peptides are pooled.")
        self.serial_radio = QRadioButton("in series")
        self.serial_radio.setToolTip("Each enzyme digests the peptides of the one before it, in the order shown.")
        self.parallel_radio.setChecked(True)
        self.combine_group = QButtonGroup(self)
        self.combine_group.addButton(self.parallel_radio)
        self.combine_group.addButton(self.serial_radio)
        combine_col.addWidget(self.parallel_radio)
        combine_col.addWidget(self.serial_radio)
        general.addWidget(self.combine_box)
        general.addStretch(1)
        row.addLayout(general)
        row.addSpacing(24)   # room between the limits and the enzymes

        # right: one panel per enzyme, side by side; the row scrolls sideways when it gets wide
        self.enzyme_panels = []
        container = QWidget()
        container.setObjectName("enzymeRow")
        self.enzyme_row = QHBoxLayout(container)
        self.enzyme_row.setContentsMargins(0, 0, 0, 0)
        self.enzyme_row.setSpacing(20)
        self.add_enzyme_button = QPushButton("+ Add enzyme")
        self.add_enzyme_button.clicked.connect(self.add_enzyme)
        self.enzyme_row.addWidget(self.add_enzyme_button, 0, Qt.AlignBottom)
        self.enzyme_row.addStretch(1)
        self.enzyme_scroll = QScrollArea()
        self.enzyme_scroll.setWidgetResizable(True)
        self.enzyme_scroll.setFrameShape(QFrame.NoFrame)
        self.enzyme_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.enzyme_scroll.setObjectName("enzymeScroll")
        # no background of its own, so the enzymes sit on the colour of the Digestion Enzyme box
        self.enzyme_scroll.setStyleSheet(
            "#enzymeScroll, #enzymeScroll > QWidget, #enzymeRow { background: transparent; }")
        self.enzyme_scroll.setWidget(container)
        row.addWidget(self.enzyme_scroll, 1)

        self.add_enzyme(DEFAULT_ENZYME)
        # as tall as a panel, plus room for the sideways scroll bar only while it is showing
        self.enzyme_scroll.horizontalScrollBar().rangeChanged.connect(self._fit_enzyme_height)
        self._fit_enzyme_height()
        col.addWidget(box)

        # fixed and variable modifications side by side; each applies to all sequences and residues
        fixed_box = QGroupBox("Fixed modifications")
        fixed_col = QVBoxLayout(fixed_box)
        self.fixed_mods = ModificationList(SUGGESTIONS)
        for mod in DEFAULT_FIXED:                  # carbamidomethyl cysteine is on by default
            self.fixed_mods.add_mod(mod.residue, mod.symbol, mod.mass)
        fixed_col.addWidget(self.fixed_mods)

        variable_box = QGroupBox("Variable modifications")
        variable_col = QVBoxLayout(variable_box)
        self.variable_mods = ModificationList(SUGGESTIONS)
        variable_col.addWidget(self.variable_mods)

        mods_row = QHBoxLayout()
        mods_row.addWidget(fixed_box)
        mods_row.addWidget(variable_box)
        col.addLayout(mods_row)
        return page

    def _species_box(self):
        box = QGroupBox("DSBU species")
        col = QVBoxLayout(box)
        self.kind_checks = {}
        for kind in KINDS:
            check = QCheckBox(kind)
            check.setChecked(True)
            self.kind_checks[kind] = check
            col.addWidget(check)
        self.mass_check = QCheckBox("Only species matching a mass")
        self.mass_check.toggled.connect(self._toggle_mass)
        col.addWidget(self.mass_check)
        form = QFormLayout()
        self.mass_spin = QDoubleSpinBox()
        self.mass_spin.setRange(0, 200000)
        self.mass_spin.setDecimals(4)
        self.mass_spin.setValue(3958.0760)
        self.mass_spin.setSuffix(" Da")
        self.ppm_spin = QDoubleSpinBox()
        self.ppm_spin.setRange(0.1, 1000)
        self.ppm_spin.setValue(10.0)
        self.ppm_spin.setSuffix(" ppm")
        self.mass_spin.setMaximumWidth(160)
        self.ppm_spin.setMaximumWidth(160)
        form.addRow("Neutral mass", self.mass_spin)
        form.addRow("Tolerance", self.ppm_spin)
        col.addLayout(form)
        self._toggle_mass(False)
        return box

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&Open FASTA...", self.open_fasta, "Ctrl+O")
        file_menu.addSeparator()
        file_menu.addAction("Export &peptides (CSV)...", self.export_peptides)
        file_menu.addAction("Export &species (CSV)...", self.export_species)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close, "Ctrl+Q")
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction("&About DeltaXL", self.about)

    # ---- actions ------------------------------------------------------------------------
    def _toggle_mass(self, enabled):
        self.mass_spin.setEnabled(enabled)
        self.ppm_spin.setEnabled(enabled)

    def open_fasta(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open FASTA file", "", "FASTA files (*.fasta *.fa *.faa *.txt);;All files (*)")
        if path:
            self.fasta_edit.setText(path)
            for protein in read_fasta(path):
                self.add_protein_box(protein, Path(path).name)

    def _limit_rows(self, parent, title, aa_value, aa_on, da_value, da_on):
        """A title and, under it: [x] amino acids  or  [x] Da. Returns the four widgets."""
        label = QLabel(title)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        aa_check, aa_spin = QCheckBox(), QSpinBox()
        aa_spin.setRange(1, 500)
        aa_spin.setValue(aa_value)
        aa_spin.setSuffix(" AA")
        da_check, da_spin = QCheckBox(), QDoubleSpinBox()
        da_spin.setRange(0, 100000)
        da_spin.setDecimals(1)
        da_spin.setValue(da_value)
        da_spin.setSuffix(" Da")
        for check, spin, on in ((aa_check, aa_spin, aa_on), (da_check, da_spin, da_on)):
            spin.setMaximumWidth(110)
            check.toggled.connect(spin.setEnabled)   # the box switches its limit on or off
            check.setChecked(on)
            spin.setEnabled(on)
        line = QHBoxLayout()
        line.addWidget(aa_check)
        line.addWidget(aa_spin)
        line.addSpacing(6)
        line.addWidget(QLabel("or"))
        line.addSpacing(6)
        line.addWidget(da_check)
        line.addWidget(da_spin)
        line.addStretch(1)
        parent.addWidget(label)
        parent.addLayout(line)
        return aa_check, aa_spin, da_check, da_spin

    def peptide_limits(self):
        """The limits that are switched on; a limit that is off is None."""
        def value(check, spin):
            return spin.value() if check.isChecked() else None
        return {"min_aa": value(self.min_aa_check, self.min_len),
                "max_aa": value(self.max_aa_check, self.max_len),
                "min_da": value(self.min_da_check, self.min_da),
                "max_da": value(self.max_da_check, self.max_da)}

    def add_enzyme(self, enzyme=None):
        """Add an enzyme panel at the right end of the row (the next preset not used yet)."""
        if not isinstance(enzyme, type(DEFAULT_ENZYME)):
            used = {panel.enzyme_combo.currentText() for panel in self.enzyme_panels}
            enzyme = next((e for e in ENZYMES if e.name not in used), DEFAULT_ENZYME)
        panel = EnzymePanel(enzyme)
        panel.removed.connect(self.remove_enzyme)
        self.enzyme_panels.append(panel)
        self.enzyme_row.insertWidget(len(self.enzyme_panels) - 1, panel, 0, Qt.AlignTop)
        self._enzymes_changed()
        self.enzyme_scroll.ensureWidgetVisible(self.add_enzyme_button)

    def _fit_enzyme_height(self, *_):
        bar = self.enzyme_scroll.horizontalScrollBar()
        room = bar.sizeHint().height() if bar.maximum() > 0 else 0
        self.enzyme_scroll.setFixedHeight(self.enzyme_panels[0].sizeHint().height() + room)

    def remove_enzyme(self, panel):
        self.enzyme_panels.remove(panel)
        panel.deleteLater()
        self._enzymes_changed()

    def _enzymes_changed(self):
        several = len(self.enzyme_panels) > 1
        self.combine_box.setVisible(several)          # in parallel / in series: only with 2+ enzymes
        for number, panel in enumerate(self.enzyme_panels, start=1):
            panel.setTitle(f"Enzyme {number}" if several else "Enzyme")
            panel.remove_button.setEnabled(several)   # the last enzyme cannot be removed

    def enzyme_mode(self):
        return "serial" if self.serial_radio.isChecked() else "parallel"

    def _has_carbamidomethyl(self):
        """True while carbamidomethyl cysteine is in the fixed modifications list."""
        return any(residue == CARBAMIDOMETHYL.residue and abs(mass - CARBAMIDOMETHYL.mass) < 0.001
                   for residue, symbol, mass in self.fixed_mods.mods())

    def _options(self):
        kinds = tuple(k for k, c in self.kind_checks.items() if c.isChecked())
        return Options(
            missed_cleavages=self.enzyme_panels[0].missed.value(),
            min_length=self.min_len.value() if self.min_aa_check.isChecked() else 1,
            max_length=self.max_len.value() if self.max_aa_check.isChecked() else None,
            carbamidomethyl=self._has_carbamidomethyl(),
            kinds=kinds,
            mass=self.mass_spin.value() if self.mass_check.isChecked() else None,
            ppm=self.ppm_spin.value(),
        )

    def run(self):
        path = self.fasta_edit.text().strip()
        if not path:
            self.step_list.setCurrentRow(0)
            QMessageBox.information(self, "DeltaXL", "Choose a FASTA file first.")
            return
        self._last_options = self._options()
        self.run_button.setEnabled(False)
        self.progress.setRange(0, 0)  # busy indicator
        self.statusBar().showMessage("Working...")
        self.worker = Worker(path, self._last_options, self)
        self.worker.done.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _finish_run(self):
        self.run_button.setEnabled(True)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)

    def _on_done(self, result):
        self._finish_run()
        self.result = result
        self.peptide_model.set_rows([peptide_row(p) for p in result.peptides])
        self.species_model.set_rows(result.species_rows)
        shown = len(result.species_rows)
        message = f"{len(result.peptides)} peptides, {result.species_total} species"
        if shown < result.species_total:
            message += f" (showing the first {shown}; the CSV export contains all)"
        self.statusBar().showMessage(message)
        self.summary.setText(message)
        self.step_list.setCurrentRow(3)  # show the results

    def _on_failed(self, message):
        self._finish_run()
        self.statusBar().showMessage("Error")
        QMessageBox.warning(self, "DeltaXL", message)

    def _ask_save(self, title, default_name):
        path, _ = QFileDialog.getSaveFileName(self, title, default_name, "CSV files (*.csv)")
        return path

    def export_peptides(self):
        if self.result is None:
            QMessageBox.information(self, "DeltaXL", "Run an analysis first.")
            return
        path = self._ask_save("Export peptides", "peptides.csv")
        if path:
            n = write_peptides_csv(self.result.peptides, path)
            self.statusBar().showMessage(f"Wrote {n} peptides to {path}")

    def export_species(self):
        if self.result is None:
            QMessageBox.information(self, "DeltaXL", "Run an analysis first.")
            return
        path = self._ask_save("Export species", "species.csv")
        if path:
            n = write_species_csv(
                iter_species(self.result.peptides, self.result.lengths, self._last_options), path)
            self.statusBar().showMessage(f"Wrote {n} species to {path}")

    def about(self):
        QMessageBox.about(
            self, "About DeltaXL",
            f"<b>DeltaXL {__version__}</b><br>Quantitative comparison of crosslinking MS datasets."
            "<br><br>Early development version.")