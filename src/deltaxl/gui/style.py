"""The look of DeltaXL: a modern, flat style with rounded rectangles and one accent colour.

It follows the system setting: light mode when your desktop is light, dark mode when it is dark,
and it switches while the program is running if you change the system setting.

To change something, edit the numbers and colours just below. To force one mode, set MODE.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPalette, QPen, QPixmap, QPolygonF

import tempfile
from pathlib import Path

MODE = "auto"   # "auto" = follow the system, or "light" / "dark" to force one

RADIUS = 8        # corners of buttons, text boxes, list items (pixels)
RADIUS_BIG = 12   # corners of the larger boxes
FONT = '"Inter", "Segoe UI", "Noto Sans", "Cantarell", "DejaVu Sans", sans-serif'

LIGHT = dict(
    BG="#f6f7f6", SURFACE="#ffffff", INPUT="#ffffff", TEXT="#1f2a28", SUB="#5b6b68",
    BORDER="#dde3e1", STRONG="#b5c1be", ACCENT="#2c5f5a", ACCENT_HOVER="#3a7a73", ACCENT_TEXT="#ffffff",
    HOVER="#eef3f2", PRESSED="#e1eae8", SEL_BG="#d6e7e4", SEL_TEXT="#1f2a28", ALT="#f9fbfa",
    HEADER="#f1f5f4", SCROLL="#b9c7c4", DISABLED="#9aa8a5", HEADING="#2c5f5a",
)
DARK = dict(
    BG="#1b1f1e", SURFACE="#232827", INPUT="#2c3231", TEXT="#e4eae8", SUB="#9aa8a5",
    BORDER="#38413f", STRONG="#566260", ACCENT="#2f7d74", ACCENT_HOVER="#3a9288", ACCENT_TEXT="#ffffff",
    HOVER="#2b3130", PRESSED="#343b3a", SEL_BG="#24504b", SEL_TEXT="#ffffff", ALT="#272c2b",
    HEADER="#2a302f", SCROLL="#4a5654", DISABLED="#6b7977", HEADING="#7cc4bb",
)

SHEET = """
* { font-family: @FONT@; font-size: 9pt; color: @TEXT@; }
QMainWindow, QDialog { background-color: @BG@; }
QWidget#central { background-color: @BG@; }

QLabel#pageTitle { font-size: 15pt; font-weight: bold; color: @HEADING@; }
QLabel#pageHint { color: @SUB@; }

/* ---- the step list on the left ---- */
QLabel#taskHeader { color: @SUB@; font-weight: bold; padding: 6px 4px; }
QListWidget#stepList { background: transparent; border: none; outline: 0; }
QListWidget#stepList::item { padding: 0px 12px; height: 38px; margin: 2px 0px; color: @TEXT@;
    border-radius: @R@px; border-left: 3px solid transparent; }
QListWidget#stepList::item:hover { background: @HOVER@; }
QListWidget#stepList::item:selected { background: @SEL_BG@; color: @SEL_TEXT@; font-weight: bold;
    border-left: 3px solid @ACCENT@; }

/* ---- menus ---- */
QMenuBar { background-color: @BG@; border-bottom: 1px solid @BORDER@; }
QMenuBar::item { padding: 5px 10px; background: transparent; border-radius: @R@px; }
QMenuBar::item:selected { background-color: @SEL_BG@; }
QMenu { background-color: @SURFACE@; border: 1px solid @BORDER@; padding: 4px; }
QMenu::item { padding: 5px 26px 5px 20px; border-radius: 6px; }
QMenu::item:selected { background-color: @SEL_BG@; color: @SEL_TEXT@; }
QMenu::separator { height: 1px; background: @BORDER@; margin: 4px 6px; }

/* ---- boxes ---- */
QGroupBox { background-color: @SURFACE@; border: 1px solid @BORDER@; border-radius: @R2@px;
    margin-top: 16px; padding: 16px 12px 10px 12px; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 14px; padding: 0 4px;
    color: @SUB@; font-weight: bold; }

/* ---- buttons ---- */
QPushButton { padding: 5px 18px; min-height: 20px; background-color: @SURFACE@; border: 1px solid @STRONG@;
    border-radius: @R@px; }
QPushButton:hover { background-color: @HOVER@; }
QPushButton:pressed { background-color: @PRESSED@; }
QPushButton:disabled { color: @DISABLED@; border-color: @BORDER@; background-color: @BG@; }
QPushButton:default, QPushButton#runButton { background-color: @ACCENT@; border: 1px solid @ACCENT@;
    color: @ACCENT_TEXT@; font-weight: bold; }
QPushButton#runButton:hover { background-color: @ACCENT_HOVER@; border-color: @ACCENT_HOVER@; }
QPushButton#runButton:pressed { background-color: @ACCENT@; }
QPushButton#runButton:disabled { background-color: @BORDER@; border-color: @BORDER@; color: @DISABLED@; }

/* ---- text boxes and spin boxes ---- */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background-color: @INPUT@; border: 1px solid @STRONG@;
    border-radius: @R@px; padding: 4px 8px; selection-background-color: @ACCENT@; selection-color: @ACCENT_TEXT@; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid @ACCENT@; }
QSpinBox, QDoubleSpinBox { padding-right: 22px; }
QSpinBox::up-button, QDoubleSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right;
    width: 20px; border: none; background: transparent; }
QSpinBox::down-button, QDoubleSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right;
    width: 20px; border: none; background: transparent; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: url(@ICONS@/up.png); width: 7px; height: 4px; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: url(@ICONS@/down.png); width: 7px; height: 4px; }
QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled { image: url(@ICONS@/up_off.png); }
QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled { image: url(@ICONS@/down_off.png); }
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { background-color: @BG@; color: @DISABLED@; border-color: @BORDER@; }

/* ---- check boxes ---- */
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; }
QCheckBox::indicator:unchecked { image: url(@ICONS@/box.png); }
QCheckBox::indicator:checked { image: url(@ICONS@/box_checked.png); }
QCheckBox::indicator:unchecked:disabled { image: url(@ICONS@/box_off.png); }
QCheckBox::indicator:checked:disabled { image: url(@ICONS@/box_checked_off.png); }
QCheckBox:disabled { color: @DISABLED@; }

/* ---- tabs ---- */
QTabWidget::pane { border: 1px solid @BORDER@; background-color: @SURFACE@; border-radius: @R@px; top: -1px; }
QTabBar::tab { padding: 7px 16px; margin-right: 2px; background: transparent; color: @SUB@;
    border: none; border-bottom: 2px solid transparent; }
QTabBar::tab:hover { color: @TEXT@; }
QTabBar::tab:selected { color: @TEXT@; font-weight: bold; border-bottom: 2px solid @ACCENT@; }

/* ---- tables ---- */
QTableView { background-color: @SURFACE@; alternate-background-color: @ALT@; gridline-color: @ALT@;
    border: none; border-radius: @R@px; selection-background-color: @SEL_BG@; selection-color: @SEL_TEXT@; }
QHeaderView::section { padding: 6px 10px; border: none; border-bottom: 1px solid @BORDER@;
    background-color: @HEADER@; color: @SUB@; font-weight: bold; }
QHeaderView::section:hover { color: @TEXT@; }
QTableCornerButton::section { background-color: @HEADER@; border: none; }

/* ---- scroll bars ---- */
QScrollBar:vertical { background: transparent; width: 12px; margin: 2px; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 2px; }
QScrollBar::handle { background-color: @SCROLL@; border-radius: 4px; min-height: 28px; min-width: 28px; }
QScrollBar::handle:hover { background-color: @STRONG@; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ---- progress bar and status bar ---- */
QProgressBar { border: none; border-radius: 3px; background-color: @BORDER@; max-height: 6px; text-align: center; }
QProgressBar::chunk { background-color: @ACCENT@; border-radius: 3px; }
QStatusBar { background-color: @BG@; border-top: 1px solid @BORDER@; color: @SUB@; }
QStatusBar::item { border: none; }
QToolTip { background-color: @SURFACE@; color: @TEXT@; border: 1px solid @STRONG@; padding: 3px; }
"""


# ---- small images drawn in code (check boxes and arrows) ------------------------------------
def _pixmap(width, height, draw):
    pm = QPixmap(width, height)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    draw(painter)
    painter.end()
    return pm


def _box(p, c, enabled=True, tick=False):
    if tick:
        fill = edge = c["ACCENT"] if enabled else c["BORDER"]
    else:
        fill, edge = (c["INPUT"], c["STRONG"]) if enabled else (c["BG"], c["BORDER"])
    p.setBrush(QColor(fill))
    p.setPen(QPen(QColor(edge), 1))
    p.drawRoundedRect(QRectF(0.5, 0.5, 15, 15), 4, 4)
    if tick:
        pen = QPen(QColor(c["ACCENT_TEXT"]), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolyline(QPolygonF([QPointF(4.3, 8.4), QPointF(6.8, 11), QPointF(11.7, 5)]))


def _arrow(p, colour, up):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(colour))
    if up:
        points = [QPointF(0, 4), QPointF(7, 4), QPointF(3.5, 0.2)]
    else:
        points = [QPointF(0, 0), QPointF(7, 0), QPointF(3.5, 3.8)]
    p.drawPolygon(QPolygonF(points))


def _write_icons(c, name):
    folder = Path(tempfile.gettempdir()) / f"deltaxl-icons-{name}"
    folder.mkdir(exist_ok=True)
    images = {
        "box": (16, 16, lambda p: _box(p, c)),
        "box_checked": (16, 16, lambda p: _box(p, c, tick=True)),
        "box_off": (16, 16, lambda p: _box(p, c, enabled=False)),
        "box_checked_off": (16, 16, lambda p: _box(p, c, enabled=False, tick=True)),
        "up": (7, 4, lambda p: _arrow(p, c["SUB"], True)),
        "down": (7, 4, lambda p: _arrow(p, c["SUB"], False)),
        "up_off": (7, 4, lambda p: _arrow(p, c["DISABLED"], True)),
        "down_off": (7, 4, lambda p: _arrow(p, c["DISABLED"], False)),
    }
    for filename, (w, h, draw) in images.items():
        _pixmap(w, h, draw).save(str(folder / f"{filename}.png"))
    return folder.as_posix()


def _palette(c):
    role, group = QPalette.ColorRole, QPalette.ColorGroup
    p = QPalette()
    colours = {
        role.Window: c["BG"], role.WindowText: c["TEXT"], role.Base: c["INPUT"],
        role.AlternateBase: c["ALT"], role.Text: c["TEXT"], role.Button: c["SURFACE"],
        role.ButtonText: c["TEXT"], role.ToolTipBase: c["SURFACE"], role.ToolTipText: c["TEXT"],
        role.PlaceholderText: c["DISABLED"], role.Highlight: c["ACCENT"], role.HighlightedText: c["ACCENT_TEXT"],
    }
    for r, colour in colours.items():
        p.setColor(r, QColor(colour))
    for r in (role.WindowText, role.Text, role.ButtonText):
        p.setColor(group.Disabled, r, QColor(c["DISABLED"]))
    return p


# ---- light or dark? ---------------------------------------------------------------------------
_state = {"system_dark": None, "applied": None, "connected": False}


def _wants_dark(app):
    """True if the window should be dark: forced by MODE, else read from the system."""
    if MODE == "dark":
        return True
    if MODE == "light":
        return False
    if _state["system_dark"] is None:  # remember how the desktop looks before we replace its palette
        _state["system_dark"] = app.palette().color(QPalette.ColorRole.Window).lightness() < 128
    try:
        scheme = app.styleHints().colorScheme()
    except AttributeError:  # Qt older than 6.5
        return _state["system_dark"]
    if scheme == Qt.ColorScheme.Dark:
        return True
    if scheme == Qt.ColorScheme.Light:
        return False
    return _state["system_dark"]  # the desktop did not say


def apply(app):
    """Apply the light or dark look, and re-apply it if the system setting changes."""
    dark = _wants_dark(app)
    if dark != _state["applied"]:
        _state["applied"] = dark
        c = LIGHT if not dark else DARK
        sheet = SHEET.replace("@FONT@", FONT).replace("@R@", str(RADIUS)).replace("@R2@", str(RADIUS_BIG))
        for key, value in c.items():
            sheet = sheet.replace(f"@{key}@", value)
        sheet = sheet.replace("@ICONS@", _write_icons(c, "dark" if dark else "light"))
        app.setStyle("Fusion")
        app.setPalette(_palette(c))
        app.setStyleSheet(sheet)
    if MODE == "auto" and not _state["connected"]:
        try:
            app.styleHints().colorSchemeChanged.connect(lambda *_: apply(app))
            _state["connected"] = True
        except AttributeError:
            pass
