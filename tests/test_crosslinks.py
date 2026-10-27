import pytest

from deltaxl.io.fasta import Protein
from deltaxl.theory.crosslinks import (DSBU, crosslinks, dead_ends, loop_links,
                                       match_mass, reactive_sites)
from deltaxl.theory.digest import digest

# Protein of 11 residues: tryptic fragments AAAK | GGGK | DDD
SEQ = "AAAKGGGKDDD"


def by_sequence(peptides, sequence):
    return next(p for p in peptides if p.sequence == sequence)


@pytest.fixture
def peps():
    return digest(Protein("p", SEQ), missed_cleavages=1)


def test_c_terminal_lysine_is_not_reactive(peps):
    # GGGK ends in K that trypsin cut, so it cannot carry a crosslink
    assert reactive_sites(by_sequence(peps, "GGGK"), DSBU, protein_length=11) == []


def test_internal_lysine_is_reactive(peps):
    # AAAKGGGK: N-terminus of the protein (1) and the internal K (4); the C-terminal K (8) is excluded
    assert reactive_sites(by_sequence(peps, "AAAKGGGK"), DSBU, protein_length=11) == [1, 4]


def test_internal_lysine_in_non_nterminal_peptide(peps):
    # GGGKDDD: internal K at position 4
    assert reactive_sites(by_sequence(peps, "GGGKDDD"), DSBU, protein_length=11) == [4]


def test_protein_c_terminal_lysine_is_reactive():
    peptides = digest(Protein("p", "AAAKGGGK"))
    last = by_sequence(peptides, "GGGK")
    assert reactive_sites(last, DSBU, protein_length=8) == [4]


def test_dead_end_mass(peps):
    pep = by_sequence(peps, "GGGKDDD")
    species = list(dead_ends([pep], DSBU))
    assert len(species) == 1
    assert species[0].mass == pytest.approx(pep.mass + 214.095357, abs=1e-6)
    assert species[0].kind == "dead-end"


def test_crosslink_mass_is_sum_plus_linker(peps):
    a = by_sequence(peps, "AAAKGGGK")   # sites 1, 4
    b = by_sequence(peps, "GGGKDDD")    # site 4
    species = list(crosslinks([a, b], DSBU))
    pairs = [s for s in species if s.peptide_a is a and s.peptide_b is b]
    assert len(pairs) == 2  # a has two sites, b has one
    for s in pairs:
        assert s.mass == pytest.approx(a.mass + b.mass + 196.084793, abs=1e-6)


def test_loop_link_needs_two_sites(peps):
    two_sites = by_sequence(peps, "AAAKGGGK")   # sites 1 and 4
    one_site = by_sequence(peps, "GGGKDDD")     # site 4 only
    assert [(s.site_a, s.site_b) for s in loop_links([two_sites], DSBU)] == [(1, 4)]
    assert list(loop_links([one_site], DSBU)) == []


def test_homodimer_pairs_listed_once(peps):
    two_sites = by_sequence(peps, "AAAKGGGK")   # sites 1 and 4
    species = list(crosslinks([two_sites], DSBU))
    # two copies of the peptide linked: (1,1), (1,4), (4,4); (4,1) is the same as (1,4)
    assert sorted((s.site_a, s.site_b) for s in species) == [(1, 1), (1, 4), (4, 4)]
    for s in species:
        assert s.mass == pytest.approx(2 * two_sites.mass + 196.084793, abs=1e-6)


def test_match_mass_within_ppm(peps):
    a = by_sequence(peps, "AAAKGGGK")
    b = by_sequence(peps, "GGGKDDD")
    species = list(crosslinks([a, b], DSBU))
    target = a.mass + b.mass + 196.084793
    hits = list(match_mass(species, target, tolerance_ppm=5))
    assert hits
    assert all(abs(h.mass - target) < target * 5e-6 for h in hits)
    assert list(match_mass(species, target + 1.0, tolerance_ppm=5)) == []
