"""Read protein sequences from FASTA files."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Protein:
    """A protein entry: header (without the leading '>') and sequence."""

    header: str
    sequence: str


def read_fasta(path):
    """Read a FASTA file and return a list of Protein objects."""
    proteins = []
    header = None
    parts = []
    with Path(path).open() as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    proteins.append(Protein(header, "".join(parts)))
                header = line[1:].strip()
                parts = []
            else:
                if header is None:
                    raise ValueError("FASTA file has sequence lines before the first header.")
                parts.append(line.replace(" ", "").upper())
    if header is not None:
        proteins.append(Protein(header, "".join(parts)))
    return proteins
