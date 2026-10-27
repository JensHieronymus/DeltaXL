from deltaxl.io.fasta import Protein
from deltaxl.theory.digest import TRYPSIN, cleavage_sites, digest, digest_all


def test_cleavage_sites_skip_before_proline():
    # K at 4 cuts, R at 8 is followed by P so it does not, K at 12 cuts
    assert cleavage_sites("AAAKGGGRPGGKDDD", TRYPSIN) == [4, 12]


def test_no_missed_cleavages():
    peptides = digest(Protein("p", "AAAKGGGRPGGKDDD"), missed_cleavages=0)
    assert [p.sequence for p in peptides] == ["AAAK", "GGGRPGGK", "DDD"]
    assert [(p.start, p.end) for p in peptides] == [(1, 4), (5, 12), (13, 15)]


def test_one_missed_cleavage_adds_joined_peptides():
    peptides = digest(Protein("p", "AAAKGGGRPGGKDDD"), missed_cleavages=1)
    assert [p.sequence for p in peptides] == [
        "AAAK", "AAAKGGGRPGGK", "GGGRPGGK", "GGGRPGGKDDD", "DDD"]
    joined = [p for p in peptides if p.missed_cleavages == 1]
    assert len(joined) == 2


def test_peptides_do_not_span_proteins():
    proteins = [Protein("a", "AAAK"), Protein("b", "GGGK")]
    peptides = digest_all(proteins, missed_cleavages=2)
    assert sorted(p.sequence for p in peptides) == ["AAAK", "GGGK"]


def test_length_filter():
    peptides = digest(Protein("p", "AAAKGGGRPGGKDDD"), min_length=5)
    assert [p.sequence for p in peptides] == ["GGGRPGGK"]


def test_mass_is_stored():
    peptide = digest(Protein("p", "AAAKGGG"), missed_cleavages=0)[0]
    assert peptide.sequence == "AAAK"
    assert peptide.mass > 0


def test_protein_nterm_flag():
    peptides = digest(Protein("p", "AAAKGGGK"))
    assert peptides[0].at_protein_nterm
    assert not peptides[1].at_protein_nterm
