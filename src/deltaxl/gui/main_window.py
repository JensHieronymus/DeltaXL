"""The main window. It only collects settings and shows results; the work is done in deltaxl.theory."""

from dataclasses import dataclass

from PySide6.QtCore import QSortFilterProxyModel, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QSpinBox, QStackedWidget, QTableView, QTabWidget, QVBoxLayout, QWidget,
)

from deltaxl import __version__
from deltaxl.gui.models import TableModel
from deltaxl.io.writers import (
    PEPTIDE_COLUMNS, SPECIES_COLUMNS, peptide_row, species_row,
    write_peptides_csv, write_species_csv,
)
from deltaxl.theory.pipeline import KINDS, Options, digest_fasta, iter_species

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
    view.horizontalHeader().setDefaultSectionSize(135)
    view.horizontalHeader().setStretchLastSection(True)
    return view, proxy


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeltaXL")
        self.resize(1100, 680)
        self.result = None
        self.worker = None
        self._last_options = None
        self._build_ui()
        self._build_menu()
        self.statusBar().showMessage("Ready...")

    # ---- layout -------------------------------------------------------------------------
    # The window is a workflow: a list of steps on the left, the page of the chosen step on the
    # right. To add a step, add its name to STEPS and add a page in _build_ui.
    STEPS = ("1.  Input", "2.  Digestion", "3.  Crosslinker", "4.  Results")

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
            0, "Input", "Choose the protein sequences to digest.", self._input_box()))
        self.pages.addWidget(self._page(
            1, "Digestion", "Set how trypsin cuts the proteins in silico.", self._digest_box()))
        self.pages.addWidget(self._page(
            2, "Crosslinker", "Choose which DSBU species to generate. Then press Run analysis.",
            self._species_box()))
        self.pages.addWidget(self._results_page())
        layout.addWidget(self.pages, 1)

        self.step_list.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.step_list.setCurrentRow(0)
        self.setCentralWidget(central)

    def _page(self, index, title, hint, content):
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
        col.addWidget(content)
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
        box = QGroupBox("Protein Sequence(s)")
        row = QHBoxLayout(box)
        self.fasta_edit = QLineEdit()
        self.fasta_edit.setPlaceholderText("FASTA file")
        browse = QPushButton("Browse...")
        browse.clicked.connect(self.open_fasta)
        row.addWidget(self.fasta_edit, 1)
        row.addWidget(browse)
        return box

    def _digest_box(self):
        box = QGroupBox("Trypsin digestion")
        form = QFormLayout(box)
        self.missed = QSpinBox()
        self.missed.setRange(0, 6)
        self.missed.setValue(2)
        self.min_len = QSpinBox()
        self.min_len.setRange(1, 100)
        self.min_len.setValue(4)
        self.max_len = QSpinBox()
        self.max_len.setRange(0, 500)
        self.max_len.setSpecialValueText("no limit")
        for spin in (self.missed, self.min_len, self.max_len):
            spin.setMaximumWidth(110)
        self.carbamidomethyl = QCheckBox("Carbamidomethyl cysteine (+57.021)")
        self.carbamidomethyl.setChecked(True)
        form.addRow("Missed cleavages", self.missed)
        form.addRow("Shortest peptide", self.min_len)
        form.addRow("Longest peptide", self.max_len)
        form.addRow(self.carbamidomethyl)
        return box

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

    def _options(self):
        kinds = tuple(k for k, c in self.kind_checks.items() if c.isChecked())
        return Options(
            missed_cleavages=self.missed.value(),
            min_length=self.min_len.value(),
            max_length=self.max_len.value() or None,
            carbamidomethyl=self.carbamidomethyl.isChecked(),
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
