"""Command-line entry point. Calls functions from the other modules."""

import argparse

from deltaxl import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="deltaxl",
        description="Quantitative comparison of crosslinking MS datasets.",
    )
    parser.add_argument("--version", action="version", version=f"deltaxl {__version__}")
    parser.parse_args(argv)
    parser.print_help()


if __name__ == "__main__":
    main()
