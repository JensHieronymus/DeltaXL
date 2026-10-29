"""A short notation for where an enzyme cuts, and the code that reads it.

An enzyme has two lines: "Cut" says where it cuts, "Unless" says where it must not.

    /     the cut. K/ is after K, /R is before R, K/D is between K and D.
          Residues beside the / must be there for the cut to happen.
    X     any residue.  K/DXL cuts after K when D, any residue and L follow.
    ( )   any one of the residues inside.  (KR)/ is the same as K/ & R/
    &     separates independent specs.  /R & K/ cuts before R and after K.

Cut line:    every spec has exactly one /.
Unless line: the same notation. A cut that matches any spec here is not made, so Unless always
             wins over Cut. A spec without a / is shorthand: its first residue is the one that
             would be cut, on either side. KP is K/P & /KP: no cut next to a K that is followed by P.

    Trypsin      cut (KR)/     unless (KR)P
    Asp-N        cut /D
"""

from dataclasses import dataclass


class RuleError(ValueError):
    """The text cannot be read; the message says why, in plain words."""


@dataclass(frozen=True)
class CutSpec:
    left: tuple    # one term per residue before the cut, the one nearest the cut last
    right: tuple   # one term per residue after the cut, the one nearest the cut first
    # a term is a frozenset of residues, or None for "any residue"


def _terms(text, spec):
    """Read the residues of one side of a spec into terms."""
    terms, i = [], 0
    while i < len(text):
        char = text[i]
        if char.isspace():
            i += 1
        elif char == "(":
            end = text.find(")", i + 1)
            if end == -1:
                raise RuleError(f"'(' in '{spec}' is never closed with ')'")
            letters = text[i + 1:end].replace(" ", "").upper()
            if not letters or not letters.isalpha():
                raise RuleError(f"Put one-letter residues between ( and ) in '{spec}'")
            terms.append(None if "X" in letters else frozenset(letters))
            i = end + 1
        elif char.isalpha():
            terms.append(None if char in "xX" else frozenset(char.upper()))
            i += 1
        else:
            raise RuleError(f"Cannot read '{char}' in '{spec}'")
    return tuple(terms)


def _parse(text, unless):
    specs = []
    for part in text.split("&"):
        part = part.strip()
        if not part:
            raise RuleError("There is an empty spec next to an &")
        if part.count("/") > 1:
            raise RuleError(f"'{part}' has more than one /; use & to cut in more than one place")
        if "/" in part:
            left, right = (_terms(side, part) for side in part.split("/"))
            if all(t is None for t in left + right):
                raise RuleError(f"'{part}' would cut everywhere; name a residue next to the /")
            specs.append(CutSpec(left, right))
        elif unless:
            # no /: the first residue is the one that would be cut, on either side of it
            terms = _terms(part, part)
            if not terms:
                raise RuleError(f"'{part}' has no residue")
            specs.append(CutSpec(terms[:1], terms[1:]))      # K/P
            specs.append(CutSpec((), terms))                 # /KP
        else:
            raise RuleError(f"'{part}' needs a / to show where the enzyme cuts")
    return specs


def parse_cut(text):
    """Read the Cut line into a list of CutSpec. Raises RuleError."""
    if not text.strip():
        raise RuleError("Write where the enzyme cuts, for example (KR)/")
    return _parse(text, unless=False)


def parse_unless(text):
    """Read the Unless line into a list of CutSpec. An empty line is fine: nothing is blocked."""
    return _parse(text, unless=True) if text.strip() else []


def _fits(term, residue):
    return term is None or residue in term


def _hit(sequence, i, spec):
    """Does the spec match for a cut just before sequence[i]?"""
    a, b = len(spec.left), len(spec.right)
    if i < a or i + b > len(sequence):
        return False
    return (all(_fits(t, sequence[i - a + k]) for k, t in enumerate(spec.left))
            and all(_fits(t, sequence[i + k]) for k, t in enumerate(spec.right)))


def cut_sites(sequence, cut, unless=""):
    """Positions i where the enzyme cuts between sequence[i-1] and sequence[i].

    cut and unless are texts, or the lists parse_cut / parse_unless return."""
    cut = parse_cut(cut) if isinstance(cut, str) else cut
    unless = parse_unless(unless) if isinstance(unless, str) else unless
    sequence = sequence.upper()
    return [i for i in range(1, len(sequence))
            if any(_hit(sequence, i, s) for s in cut)
            and not any(_hit(sequence, i, s) for s in unless)]
