"""Digestion enzymes offered in the "Digestion and Modifications" step.

An enzyme is a name and two lines in the notation described in deltaxl/theory/cleavage.py:
"cut" says where it cuts, "unless" says where it must not. Add or edit lines here; the window
picks them up without further changes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Enzyme:
    name: str
    cut: str
    unless: str = ""
    custom: bool = False    # True for an enzyme the user named in the window


ENZYMES = [
    Enzyme("Trypsin", "(KR)/", "(KR)P"),
    Enzyme("Trypsin/P", "(KR)/"),
    Enzyme("Lys-C", "K/"),
    Enzyme("Arg-C", "R/", "RP"),
    Enzyme("Glu-C", "E/"),
    Enzyme("Asp-N", "/D"),
    Enzyme("Chymotrypsin", "(FYW)/", "(FYW)P"),
]

DEFAULT_ENZYME = ENZYMES[0]

# shown when hovering the ? next to "Cut" and "Unless"
CUT_HELP = (
    "<b>Cut</b><br>"
    "<tt>/</tt> marks where the enzyme cuts: <tt>K/</tt> after K, <tt>/R</tt> before R.<br>"
    "Residues beside the <tt>/</tt> must be there for it to cut: <tt>K/D</tt> cuts between K and D.<br>"
    "<tt>X</tt> is any residue: <tt>K/DXL</tt> cuts after K when D, any residue and L follow.<br>"
    "<tt>( )</tt> is any one of the residues inside: <tt>(KR)/</tt> is the same as <tt>K/ &amp; R/</tt><br>"
    "<tt>&amp;</tt> separates cuts: <tt>/R &amp; K/</tt> cuts before R and after K.<br><br>"
    "<b>Examples</b><br>"
    "Trypsin &nbsp;&nbsp;&nbsp;<tt>(KR)/</tt><br>"
    "Asp-N &nbsp;&nbsp;&nbsp;&nbsp;<tt>/D</tt><br>"
    "After a K that follows D &nbsp;<tt>DK/</tt>"
)

UNLESS_HELP = (
    "<b>Unless</b><br>"
    "Cuts that match here are not made, even if Cut asks for them. Same notation as Cut.<br>"
    "<tt>K/P</tt> no cut between K and P.<br>"
    "Without a <tt>/</tt>, the first residue is the one that would be cut, on either side:<br>"
    "<tt>KP</tt> is the same as <tt>K/P &amp; /KP</tt>.<br>"
    "<tt>&amp;</tt> separates specs, <tt>( )</tt> and <tt>X</tt> work as in Cut.<br><br>"
    "<b>Examples</b><br>"
    "Trypsin does not cut before P &nbsp;<tt>(KR)P</tt><br>"
    "Not in C-K-D &nbsp;<tt>CK/D</tt><br>"
    "Leave empty to block nothing."
)
