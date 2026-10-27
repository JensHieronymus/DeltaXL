import csv

import pytest

from deltaxl import __version__
from deltaxl.cli import main

FASTA = ">test\nAAAKGGGKDDD\n"


def read_rows(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture
def fasta(tmp_path):
    path = tmp_path / "test.fasta"
    path.write_text(FASTA)
    return path


def test_version_string():
    assert isinstance(__version__, str)
    assert __version__.count(".") == 2


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_arguments_prints_help(capsys):
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_digest_writes_peptides(fasta, tmp_path):
    out = tmp_path / "peptides.csv"
    assert main(["digest", str(fasta), "-o", str(out),
                 "--missed-cleavages", "0", "--min-length", "1"]) == 0
    rows = read_rows(out)
    assert [r["sequence"] for r in rows] == ["AAAK", "GGGK", "DDD"]
    assert rows[0]["start"] == "1" and rows[0]["end"] == "4"


def test_crosslinks_writes_all_kinds(fasta, tmp_path):
    out = tmp_path / "species.csv"
    assert main(["crosslinks", str(fasta), "-o", str(out),
                 "--missed-cleavages", "1", "--min-length", "1"]) == 0
    kinds = {r["kind"] for r in read_rows(out)}
    assert kinds == {"crosslink", "loop-link", "dead-end"}


def test_crosslinks_kinds_filter(fasta, tmp_path):
    out = tmp_path / "species.csv"
    main(["crosslinks", str(fasta), "-o", str(out), "--missed-cleavages", "1",
          "--min-length", "1", "--kinds", "dead-end"])
    assert {r["kind"] for r in read_rows(out)} == {"dead-end"}


def test_crosslinks_mass_filter(fasta, tmp_path):
    all_out = tmp_path / "all.csv"
    main(["crosslinks", str(fasta), "-o", str(all_out), "--missed-cleavages", "1",
          "--min-length", "1"])
    target = float(read_rows(all_out)[0]["mass"])
    out = tmp_path / "filtered.csv"
    main(["crosslinks", str(fasta), "-o", str(out), "--missed-cleavages", "1",
          "--min-length", "1", "--mass", str(target), "--ppm", "1"])
    rows = read_rows(out)
    assert rows
    assert all(abs(float(r["mass"]) - target) < target * 1e-6 + 1e-6 for r in rows)
    assert len(rows) < len(read_rows(all_out))


def test_missing_file_returns_error(tmp_path, capsys):
    code = main(["digest", str(tmp_path / "nope.fasta"), "-o", str(tmp_path / "x.csv")])
    assert code == 1
    assert "error" in capsys.readouterr().err.lower()


def test_empty_fasta_returns_error(tmp_path, capsys):
    empty = tmp_path / "empty.fasta"
    empty.write_text("")
    assert main(["digest", str(empty), "-o", str(tmp_path / "x.csv")]) == 1
