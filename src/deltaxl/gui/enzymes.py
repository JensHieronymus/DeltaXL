"""Digestion enzymes offered in the "Modifications and Digestion" step.

An enzyme is a cleavage rule: which residues it cuts at, on which side of them, and when it
does not cut. Add or edit lines here; the window picks them up without further changes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Enzyme:
    name: str
    side: str          # "after": cuts on the C-terminal side of the residues, "before": on the N-terminal side
    residues: str      # one-letter codes that trigger a cut, e.g. "KR"
    exceptions: str    # no cut if the neighbouring residue is one of these (after: the next one,
                       # before: the previous one), e.g. "P"


ENZYMES = [
    Enzyme("Trypsin", "after", "KR", "P"),
    Enzyme("Trypsin/P", "after", "KR", ""),
    Enzyme("Lys-C", "after", "K", ""),
    Enzyme("Arg-C", "after", "R", "P"),
    Enzyme("Glu-C", "after", "E", ""),
    Enzyme("Asp-N", "before", "D", ""),
    Enzyme("Chymotrypsin", "after", "FYW", "P"),
]

DEFAULT_ENZYME = ENZYMES[0]
