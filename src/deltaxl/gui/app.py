"""Starts the graphical interface."""

import sys


def main():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("The graphical interface needs PySide6. Install it with:\n"
              '    pip install "deltaxl[gui]"', file=sys.stderr)
        return 1
    from deltaxl.gui import style
    from deltaxl.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("DeltaXL")
    style.apply(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
