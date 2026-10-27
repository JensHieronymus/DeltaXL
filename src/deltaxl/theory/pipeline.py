"""High-level steps shared by the command line and the graphical interface."""

from dataclasses import dataclass
from itertools import chain

from deltaxl.chemistry import CARBAMIDOMETHYL_C
from deltaxl.io.fasta import read_fasta
from deltaxl.theory.crosslinks import DSBU, crosslinks, dead_ends, loop_links, match_mass
from deltaxl.theory.digest import digest_all

KINDS = ("crosslink", "loop-link", "dead-end")


@dataclass(frozen=True)
class Options:
    """Settings for digestion and crosslink generation."""

    missed_cleavages: int = 2
    min_length: int = 4
    max_length: int | None = None
    carbamidomethyl: bool = True
    kinds: tuple = KINDS
    mass: float | None = None
    ppm: float = 10.0


def digest_fasta(path, options):
    """Read a FASTA file and digest it. Returns (peptides, protein_lengths)."""
    proteins = read_fasta(path)
    if not proteins:
        raise ValueError(f"No protein sequences found in {path}")
    fixed = CARBAMIDOMETHYL_C if options.carbamidomethyl else {}
    peptides = digest_all(proteins, missed_cleavages=options.missed_cleavages,
                          min_length=options.min_length, max_length=options.max_length,
                          fixed_mods=fixed)
    lengths = {p.header: len(p.sequence) for p in proteins}
    return peptides, lengths


def iter_species(peptides, lengths, options, crosslinker=DSBU):
    """Generate the requested crosslinked species, optionally filtered by mass."""
    generators = []
    if "crosslink" in options.kinds:
        generators.append(crosslinks(peptides, crosslinker, lengths))
    if "loop-link" in options.kinds:
        generators.append(loop_links(peptides, crosslinker, lengths))
    if "dead-end" in options.kinds:
        generators.append(dead_ends(peptides, crosslinker, lengths))
    species = chain.from_iterable(generators)
    if options.mass is not None:
        species = match_mass(species, options.mass, options.ppm)
    return species
