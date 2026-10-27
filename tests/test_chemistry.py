import pytest

from deltaxl.chemistry import CARBAMIDOMETHYL_C, PROTON, mz, peptide_mass


def test_peptide_mass_matches_known_value():
    # PEPTIDE has a monoisotopic mass of 799.3600 Da (commonly used reference value)
    assert peptide_mass("PEPTIDE") == pytest.approx(799.3600, abs=1e-3)


def test_single_glycine():
    assert peptide_mass("G") == pytest.approx(57.021464 + 18.010565, abs=1e-5)


def test_carbamidomethyl_adds_mass_per_cysteine():
    plain = peptide_mass("ACCK")
    modified = peptide_mass("ACCK", CARBAMIDOMETHYL_C)
    assert modified - plain == pytest.approx(2 * 57.021464, abs=1e-5)


def test_unknown_residue_raises():
    with pytest.raises(ValueError):
        peptide_mass("AXK")


def test_mz_singly_and_doubly_charged():
    assert mz(1000.0, 1) == pytest.approx(1000.0 + PROTON)
    assert mz(1000.0, 2) == pytest.approx((1000.0 + 2 * PROTON) / 2)


def test_mz_rejects_zero_charge():
    with pytest.raises(ValueError):
        mz(1000.0, 0)
