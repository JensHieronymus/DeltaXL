"""Command-line interface. Parses arguments and calls functions from the other modules."""

import argparse
import sys

from deltaxl import __version__
from deltaxl.io.writers import write_peptides_csv, write_species_csv
from deltaxl.theory.pipeline import KINDS, Options, digest_fasta, iter_species


def _add_digest_options(parser):
    parser.add_argument("fasta", help="FASTA file with the protein sequences")
    parser.add_argument("-o", "--output", required=True, help="CSV file to write")
    parser.add_argument("--missed-cleavages", type=int, default=2, metavar="N",
                        help="allowed missed cleavages (default: 2)")
    parser.add_argument("--min-length", type=int, default=4, metavar="N",
                        help="shortest peptide to keep (default: 4)")
    parser.add_argument("--max-length", type=int, default=None, metavar="N",
                        help="longest peptide to keep (default: no limit)")
    parser.add_argument("--no-carbamidomethyl", action="store_true",
                        help="do not add carbamidomethyl (+57.021) to cysteine")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="deltaxl",
        description="Quantitative comparison of crosslinking MS datasets.",
    )
    parser.add_argument("--version", action="version", version=f"deltaxl {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_digest = sub.add_parser("digest", help="digest proteins into tryptic peptides")
    _add_digest_options(p_digest)

    p_xl = sub.add_parser("crosslinks",
                          help="generate theoretical DSBU crosslinked peptides from a FASTA file")
    _add_digest_options(p_xl)
    p_xl.add_argument("--kinds", nargs="+", choices=KINDS, default=list(KINDS),
                      help="which species to generate (default: all)")
    p_xl.add_argument("--mass", type=float, default=None,
                      help="only keep species with this neutral mass (Da)")
    p_xl.add_argument("--ppm", type=float, default=10.0,
                      help="mass tolerance in ppm when --mass is used (default: 10)")
    return parser


def _options(args):
    return Options(
        missed_cleavages=args.missed_cleavages,
        min_length=args.min_length,
        max_length=args.max_length,
        carbamidomethyl=not args.no_carbamidomethyl,
        kinds=tuple(getattr(args, "kinds", KINDS)),
        mass=getattr(args, "mass", None),
        ppm=getattr(args, "ppm", 10.0),
    )


def run_digest(args):
    peptides, _ = digest_fasta(args.fasta, _options(args))
    n = write_peptides_csv(peptides, args.output)
    print(f"Wrote {n} peptides to {args.output}")


def run_crosslinks(args):
    options = _options(args)
    peptides, lengths = digest_fasta(args.fasta, options)
    n = write_species_csv(iter_species(peptides, lengths, options), args.output)
    print(f"{len(peptides)} peptides -> wrote {n} species to {args.output}")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        {"digest": run_digest, "crosslinks": run_crosslinks}[args.command](args)
    except (OSError, ValueError) as error:
        print(f"deltaxl: error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
