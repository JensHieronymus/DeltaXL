"""Smoke tests for the graphical interface. Skipped when PySide6 is not installed."""

import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from deltaxl.gui import style  # noqa: E402
from deltaxl.gui.main_window import MainWindow  # noqa: E402


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    style.apply(application)
    return application


@pytest.fixture
def fasta(tmp_path):
    path = tmp_path / "t.fasta"
    path.write_text(">test\nAAAKGGGKDDD\n")
    return path


def wait_for(window, app):
    window.worker.wait()
    app.processEvents()


def test_run_fills_tables(app, fasta):
    window = MainWindow()
    window.fasta_edit.setText(str(fasta))
    window.missed.setValue(1)
    window.min_len.setValue(1)
    window.run()
    wait_for(window, app)
    assert window.peptide_model.rowCount() == 5
    assert window.species_model.rowCount() > 0
    assert window.run_button.isEnabled()


def test_missing_file_re_enables_button(app, tmp_path, monkeypatch):
    shown = []
    monkeypatch.setattr("deltaxl.gui.main_window.QMessageBox.warning",
                        lambda *args: shown.append(args[2]))
    window = MainWindow()
    window.fasta_edit.setText(str(tmp_path / "missing.fasta"))
    window.run()
    wait_for(window, app)
    assert shown
    assert window.run_button.isEnabled()


def test_kind_filter(app, fasta):
    window = MainWindow()
    window.fasta_edit.setText(str(fasta))
    window.missed.setValue(1)
    window.min_len.setValue(1)
    window.kind_checks["crosslink"].setChecked(False)
    window.kind_checks["loop-link"].setChecked(False)
    window.run()
    wait_for(window, app)
    kinds = {row[0] for row in window.species_model._rows}
    assert kinds == {"dead-end"}
