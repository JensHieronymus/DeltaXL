"""Generate theoretical crosslinked peptide species from digested peptides.

Three kinds of species are generated:
  * crosslink  : two peptides joined by the crosslinker
  * loop-link  : one peptide with both ends of the crosslinker attached to it
  * dead-end   : one peptide with a hydrolysed (water-quenched) crosslinker on one site
"""

from dataclasses import dataclass
from itertools import combinations_with_replacement


@dataclass(frozen=True)
class Crosslinker:
    """Crosslinker description. Masses are the net monoisotopic mass added (Da)."""

    name: str
    crosslink_mass: float
    deadend_mass: float
    residues: str = "K"
    nterm_reactive: bool = True


# DSBU: C9H12N2O3 net addition for a crosslink, +H2O for a hydrolysed dead-end.
DSBU = Crosslinker("DSBU", crosslink_mass=196.084793, deadend_mass=214.095357)


@dataclass(frozen=True)
class Species:
    """A theoretical crosslinked species.

    sites are 1-based positions within each peptide. For a dead-end, peptide_b and
    site_b are None. For a loop-link, peptide_b is peptide_a.
    """

    kind: str  # "crosslink", "loop-link" or "dead-end"
    peptide_a: object
    site_a: int
    peptide_b: object
    site_b: int
    mass: float


def reactive_sites(peptide, crosslinker=DSBU, protein_length=None):
    """1-based positions in the peptide that the crosslinker can react with.

    A modified lysine is not cleaved by trypsin, so a lysine at the C-terminus of a
    peptide is only a candidate when the peptide ends the protein (protein_length given).
    The peptide's N-terminal amine is only reactive at the protein N-terminus.
    """
    sites = []
    if crosslinker.nterm_reactive and peptide.at_protein_nterm:
        sites.append(1)
    for index, residue in enumerate(peptide.sequence, start=1):
        if residue not in crosslinker.residues:
            continue
        is_c_terminal = index == len(peptide.sequence)
        if is_c_terminal and not (protein_length is not None and peptide.end == protein_length):
            continue
        sites.append(index)
    return sites


def dead_ends(peptides, crosslinker=DSBU, protein_lengths=None):
    """Peptides carrying a hydrolysed crosslinker on one site."""
    lengths = protein_lengths or {}
    for pep in peptides:
        for site in reactive_sites(pep, crosslinker, lengths.get(pep.protein)):
            yield Species("dead-end", pep, site, None, None, pep.mass + crosslinker.deadend_mass)


def loop_links(peptides, crosslinker=DSBU, protein_lengths=None):
    """Peptides with both ends of the crosslinker on two different sites of the same peptide."""
    lengths = protein_lengths or {}
    for pep in peptides:
        sites = reactive_sites(pep, crosslinker, lengths.get(pep.protein))
        for i, a in enumerate(sites):
            for b in sites[i + 1:]:
                yield Species("loop-link", pep, a, pep, b, pep.mass + crosslinker.crosslink_mass)


def crosslinks(peptides, crosslinker=DSBU, protein_lengths=None):
    """All pairs of peptides joined by the crosslinker, at every combination of sites.

    A peptide may be paired with a second copy of itself (homodimer link); each such
    species is listed once. Links within a single peptide are returned by loop_links().
    """
    lengths = protein_lengths or {}
    site_cache = {id(p): reactive_sites(p, crosslinker, lengths.get(p.protein)) for p in peptides}
    for pep_a, pep_b in combinations_with_replacement(peptides, 2):
        for site_a in site_cache[id(pep_a)]:
            for site_b in site_cache[id(pep_b)]:
                if pep_a is pep_b and site_b < site_a:
                    continue  # two copies of the same peptide: (a, b) and (b, a) are the same species
                mass = pep_a.mass + pep_b.mass + crosslinker.crosslink_mass
                yield Species("crosslink", pep_a, site_a, pep_b, site_b, mass)


def match_mass(species_iter, target_mass, tolerance_ppm=10.0):
    """Keep species whose mass is within tolerance_ppm of target_mass."""
    tol = target_mass * tolerance_ppm / 1e6
    for sp in species_iter:
        if abs(sp.mass - target_mass) <= tol:
            yield sp
