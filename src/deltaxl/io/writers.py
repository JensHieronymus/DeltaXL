"""Write results to CSV files, and turn results into table rows."""

import csv
from pathlib import Path

PEPTIDE_COLUMNS = ["protein", "start", "end", "sequence", "missed_cleavages", "mass"]

SPECIES_COLUMNS = [
    "kind", "mass",
    "protein_a", "start_a", "end_a", "sequence_a", "site_a", "residue_a",
    "protein_b", "start_b", "end_b", "sequence_b", "site_b", "residue_b",
]


def peptide_row(p):
    """One table row (raw values) for a Peptide."""
    return [p.protein, p.start, p.end, p.sequence, p.missed_cleavages, p.mass]


def species_row(sp):
    """One table row (raw values) for a crosslinked species.

    site_* is the position within the peptide; residue_* is the position within the protein.
    """
    a, b = sp.peptide_a, sp.peptide_b
    row = [sp.kind, sp.mass,
           a.protein, a.start, a.end, a.sequence, sp.site_a, a.start + sp.site_a - 1]
    if b is None:
        row += ["", "", "", "", "", ""]
    else:
        row += [b.protein, b.start, b.end, b.sequence, sp.site_b, b.start + sp.site_b - 1]
    return row


def write_peptides_csv(peptides, path):
    """Write Peptide objects to a CSV file. Returns the number of rows written."""
    count = 0
    with Path(path).open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(PEPTIDE_COLUMNS)
        for p in peptides:
            row = peptide_row(p)
            row[5] = f"{row[5]:.6f}"
            writer.writerow(row)
            count += 1
    return count


def write_species_csv(species, path):
    """Write crosslinked species to a CSV file as they are generated. Returns the row count."""
    count = 0
    with Path(path).open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(SPECIES_COLUMNS)
        for sp in species:
            row = species_row(sp)
            row[1] = f"{row[1]:.6f}"
            writer.writerow(row)
            count += 1
    return count
