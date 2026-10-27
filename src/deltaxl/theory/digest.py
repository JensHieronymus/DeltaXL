"""In-silico enzymatic digestion of proteins."""

from dataclasses import dataclass

from deltaxl.chemistry import CARBAMIDOMETHYL_C, peptide_mass
from deltaxl.io.fasta import Protein


@dataclass(frozen=True)
class Enzyme:
    """Cleaves after any residue in `cleaves_after`, unless the next residue is in `blocked_before`."""

    name: str
    cleaves_after: str
    blocked_before: str = ""


TRYPSIN = Enzyme("trypsin", cleaves_after="KR", blocked_before="P")


@dataclass(frozen=True)
class Peptide:
    """A peptide from a protein. Positions are 1-based and inclusive."""

    protein: str
    sequence: str
    start: int
    end: int
    missed_cleavages: int
    mass: float

    @property
    def at_protein_nterm(self):
        return self.start == 1


def cleavage_sites(sequence, enzyme=TRYPSIN):
    """Return the 1-based positions after which the enzyme cuts (never the last residue)."""
    sites = []
    for pos in range(1, len(sequence)):  # position of residue (1-based); excludes the last residue
        residue = sequence[pos - 1]
        next_residue = sequence[pos]
        if residue in enzyme.cleaves_after and next_residue not in enzyme.blocked_before:
            sites.append(pos)
    return sites


def digest(protein, enzyme=TRYPSIN, missed_cleavages=0, min_length=1, max_length=None,
           fixed_mods=CARBAMIDOMETHYL_C):
    """Digest one Protein into peptides, including peptides with missed cleavages.

    Peptides never span two proteins. Returns a list sorted by start then end position.
    """
    if not isinstance(protein, Protein):
        raise TypeError("digest() expects a Protein object")
    seq = protein.sequence
    boundaries = [0] + cleavage_sites(seq, enzyme) + [len(seq)]
    # fragment i covers residues boundaries[i]+1 .. boundaries[i+1]
    peptides = []
    n_fragments = len(boundaries) - 1
    for i in range(n_fragments):
        for missed in range(missed_cleavages + 1):
            j = i + missed
            if j >= n_fragments:
                break
            start = boundaries[i] + 1
            end = boundaries[j + 1]
            length = end - start + 1
            if length < min_length or (max_length is not None and length > max_length):
                continue
            sub = seq[start - 1:end]
            peptides.append(Peptide(protein.header, sub, start, end, missed,
                                    peptide_mass(sub, fixed_mods)))
    peptides.sort(key=lambda p: (p.start, p.end))
    return peptides


def digest_all(proteins, **kwargs):
    """Digest a list of proteins and return one flat list of peptides."""
    result = []
    for protein in proteins:
        result.extend(digest(protein, **kwargs))
    return result
