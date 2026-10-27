"""Windows Vista / Windows 7 "Aero"-style look, applied with a Qt stylesheet."""

STYLESHEET = """
* {
    font-family: "Segoe UI", "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 9pt;
    color: #1e1e1e;
}

QMainWindow, QDialog {
    background-color: #dbe6f4;
}

QWidget#central {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e9f0f9, stop:1 #d3e0f1);
}

QMenuBar {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f6f9fd, stop:1 #dfe8f4);
    border-bottom: 1px solid #a9b9cf;
}
QMenuBar::item { padding: 4px 9px; background: transparent; }
QMenuBar::item:selected {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f4faff, stop:1 #cfe7fa);
    border: 1px solid #7da2ce;
    border-radius: 3px;
}
QMenu {
    background-color: #f2f2f2;
    border: 1px solid #979797;
}
QMenu::item { padding: 4px 28px 4px 24px; }
QMenu::item:selected {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f6fbff, stop:1 #d4ebfb);
    border: 1px solid #a8d8f0;
    border-radius: 3px;
}
QMenu::separator { height: 1px; background: #d9d9d9; margin: 3px 2px 3px 24px; }

QGroupBox {
    background-color: rgba(255, 255, 255, 150);
    border: 1px solid #a8bbd3;
    border-radius: 4px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #1c3e72;
    font-weight: bold;
}

QPushButton {
    padding: 4px 16px;
    min-height: 20px;
    color: #1e1e1e;
    border: 1px solid #707070;
    border-radius: 3px;
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f2f2f2, stop:0.49 #ebebeb, stop:0.5 #dddddd, stop:1 #cfcfcf);
}
QPushButton:hover {
    border: 1px solid #3c7fb1;
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #eaf6fd, stop:0.49 #d9f0fc, stop:0.5 #bee6fd, stop:1 #a7d9f5);
}
QPushButton:pressed {
    border: 1px solid #2c628b;
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e5f4fc, stop:0.49 #c4e5f6, stop:0.5 #98d1ef, stop:1 #68b3db);
}
QPushButton:disabled {
    color: #8a8a8a;
    border: 1px solid #adb2b5;
    background-color: #f4f4f4;
}
QPushButton:default, QPushButton#runButton {
    border: 1px solid #3c7fb1;
    font-weight: bold;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: white;
    border: 1px solid #abadb3;
    border-top-color: #e2e3ea;
    border-radius: 2px;
    padding: 2px 4px;
    selection-background-color: #3399ff;
    selection-color: white;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #3c7fb1;
}
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #f0f0f0;
    color: #8a8a8a;
}

QCheckBox { spacing: 6px; }
QCheckBox::indicator {
    width: 13px; height: 13px;
    border: 1px solid #8e8f8f;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #dcdcdc, stop:1 #ffffff);
}
QCheckBox::indicator:hover { border: 1px solid #3c7fb1; }
QCheckBox::indicator:checked {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #d0e9fb, stop:1 #4a9bd6);
    border: 1px solid #2c628b;
}

QTabWidget::pane {
    border: 1px solid #898c95;
    background-color: white;
    top: -1px;
}
QTabBar::tab {
    padding: 5px 16px;
    margin-right: 2px;
    border: 1px solid #898c95;
    border-bottom: none;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f2f2f2, stop:1 #dcdcdc);
}
QTabBar::tab:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #eaf6fd, stop:1 #bde5fb);
    border-color: #3c7fb1;
}
QTabBar::tab:selected {
    background-color: white;
    border-top: 2px solid #f0b536;
    padding-bottom: 6px;
}

QTableView {
    background-color: white;
    alternate-background-color: #f4f8fd;
    gridline-color: #e6ebf1;
    border: none;
    selection-background-color: #cde8ff;
    selection-color: #1e1e1e;
}
QTableView::item:selected { border: 1px solid #7da2ce; }
QHeaderView::section {
    padding: 4px 8px;
    border: none;
    border-right: 1px solid #d5d5d5;
    border-bottom: 1px solid #d5d5d5;
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #e4ebf5);
}
QHeaderView::section:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #eaf6fd, stop:1 #bde5fb);
}

QScrollBar:vertical { background: #f0f0f0; width: 17px; border-left: 1px solid #e2e3ea; }
QScrollBar:horizontal { background: #f0f0f0; height: 17px; border-top: 1px solid #e2e3ea; }
QScrollBar::handle {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f4f4f4, stop:1 #cfcfcf);
    border: 1px solid #979797;
    border-radius: 2px;
    min-height: 24px; min-width: 24px;
}
QScrollBar::handle:hover { border-color: #3c7fb1; background-color: #bde5fb; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }

QProgressBar {
    border: 1px solid #a2a2a2;
    border-radius: 2px;
    background-color: #e6e6e6;
    text-align: center;
    height: 14px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #b4ecab, stop:0.5 #37c91e, stop:1 #26a410);
}

QStatusBar {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e9f0f9, stop:1 #cfdcee);
    border-top: 1px solid #a9b9cf;
}
QStatusBar::item { border: none; }

QToolTip {
    background-color: #ffffe1;
    color: #1e1e1e;
    border: 1px solid #767676;
}
"""


def apply(app):
    """Use the Fusion base style (identical on every platform) plus the Aero stylesheet."""
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
