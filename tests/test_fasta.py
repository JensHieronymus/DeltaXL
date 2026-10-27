import pytest

from deltaxl.io.fasta import read_fasta


def test_read_fasta_two_entries(tmp_path):
    f = tmp_path / "x.fasta"
    f.write_text(">heavy chain\nAAAK\nGGGR\n\n>light chain\nDDD\n")
    proteins = read_fasta(f)
    assert [p.header for p in proteins] == ["heavy chain", "light chain"]
    assert [p.sequence for p in proteins] == ["AAAKGGGR", "DDD"]


def test_read_fasta_uppercases_and_strips_spaces(tmp_path):
    f = tmp_path / "x.fasta"
    f.write_text(">p\naak g\n")
    assert read_fasta(f)[0].sequence == "AAKG"


def test_sequence_before_header_raises(tmp_path):
    f = tmp_path / "x.fasta"
    f.write_text("AAAK\n>p\nGGG\n")
    with pytest.raises(ValueError):
        read_fasta(f)
