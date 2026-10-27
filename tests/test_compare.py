import pytest

from deltaxl.analysis.compare import fold_change


def test_fold_change_doubles():
    assert fold_change(100, 200) == 2


def test_fold_change_halves():
    assert fold_change(200, 100) == 0.5


def test_fold_change_zero_reference_raises():
    with pytest.raises(ValueError):
        fold_change(0, 200)
