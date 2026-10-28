"""Common modifications, offered as suggestions in the "Modifications and Digestion" step.

Each one is a residue, the new symbol it gets, and the mass change in Da (monoisotopic).
Add or remove lines here; the window picks them up without further changes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Modification:
    name: str
    residue: str    # one-letter code of the residue that carries it
    symbol: str     # the new symbol shown for the modified residue
    mass: float     # mass change in Da

    def label(self):
        return f"{self.name}   ({self.residue} → {self.symbol}, {self.mass:+.4f} Da)"


CARBAMIDOMETHYL = Modification("Carbamidomethyl", "C", "Cam", 57.0215)

# already in the fixed list when the program starts
DEFAULT_FIXED = [CARBAMIDOMETHYL]

# offered in both the fixed and the variable list
SUGGESTIONS = [
    CARBAMIDOMETHYL,
    Modification("Propionamide", "C", "Cpr", 71.0371),
    Modification("Methylthio", "C", "Cmt", 45.9877),
    Modification("Oxidation", "M", "Mox", 15.9949),
    Modification("Phospho", "S", "pS", 79.9663),
    Modification("Phospho", "T", "pT", 79.9663),
    Modification("Phospho", "Y", "pY", 79.9663),
    Modification("Deamidation", "N", "Nde", 0.9840),
    Modification("Deamidation", "Q", "Qde", 0.9840),
    Modification("Acetyl", "K", "Kac", 42.0106),
    Modification("Methyl", "K", "Kme", 14.0157),
    Modification("Dimethyl", "K", "Kme2", 28.0313),
    Modification("Trimethyl", "K", "Kme3", 42.0470),
    Modification("GlyGly (ubiquitin remnant)", "K", "Kgg", 114.0429),
    Modification("Pyro-glu from Q", "Q", "Qpg", -17.0265),
    Modification("Pyro-glu from E", "E", "Epg", -18.0106),
]