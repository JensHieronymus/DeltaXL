"""Basic chemistry: residue masses and peptide masses (monoisotopic, in Da)."""

PROTON = 1.007276466
WATER = 18.010564684

RESIDUE_MASS = {
    "G": 57.021463735,
    "A": 71.037113805,
    "S": 87.032028405,
    "P": 97.052763875,
    "V": 99.068413945,
    "T": 101.047678505,
    "C": 103.009184505,
    "L": 113.084064015,
    "I": 113.084064015,
    "N": 114.042927470,
    "D": 115.026943065,
    "Q": 128.058577540,
    "K": 128.094963050,
    "E": 129.042593135,
    "M": 131.040484645,
    "H": 137.058911875,
    "F": 147.068413945,
    "R": 156.101111050,
    "Y": 163.063328575,
    "W": 186.079312980,
}

# Fixed modifications added to a residue every time it occurs.
# Carbamidomethylation of cysteine is the usual alkylation in XL-MS workflows.
CARBAMIDOMETHYL_C = {"C": 57.021464}


def peptide_mass(sequence, fixed_mods=None):
    """Neutral monoisotopic mass of a peptide.

    fixed_mods maps a residue letter to a mass added to every occurrence,
    for example {"C": 57.021464}. Raises ValueError for unknown residues.
    """
    mods = fixed_mods or {}
    total = WATER
    for residue in sequence:
        try:
            total += RESIDUE_MASS[residue] + mods.get(residue, 0.0)
        except KeyError:
            raise ValueError(f"Unknown residue {residue!r} in sequence {sequence!r}") from None
    return total


def mz(neutral_mass, charge):
    """m/z of an ion with the given neutral mass and charge state."""
    if charge < 1:
        raise ValueError("charge must be at least 1")
    return (neutral_mass + charge * PROTON) / charge
