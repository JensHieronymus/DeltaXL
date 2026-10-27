# DeltaXL

**Quantitative comparison of crosslinking mass spectrometry (XL-MS) datasets.**

DeltaXL compares crosslink abundance across conditions, replicates and datasets, to make small structural changes in proteins visible and measurable.

> **Status: early development.** The interface and features below describe the planned scope and may change.

## What it does

- In-silico cleavage of proteins and creates a list of all possible crosslinked species
- Searches multiple MZML, MZXML or MGF files for crosslinked species
- Compares crosslinks across samples
- Exports in-silico, in-vitro and other results crosslinks as CSV tables or figures


## Installation

```
pip install deltaxl
```


## Quick start

Compare two conditions from the command line:

```
deltaxl compare condition_a.csv condition_b.csv --output delta.csv
```

A graphical interface is planned:

```
deltaxl-gui
```

## Input and output

**Input:** crosslink result tables from your search engine, one file per run or condition. Supported formats: *to be listed.*

**Output:** a CSV table with one row per crosslink and columns for abundance in each condition, fold change, replicate variation and distance (if a structure is given). *Column descriptions to be added.*

## Example

A small example dataset and a worked example will be placed in the `examples/` folder.

## Project structure

```
src/deltaxl/     the package (readers, analysis, plots, GUI)
tests/           automated tests
examples/        example data and walkthrough
docs/            extra documentation
```

## Tests

```
pip install -e ".[dev]"
pytest
```

## How to cite

If you use DeltaXL in your work, please cite:

> Hieronymus, J., Højrup, P. "Chemical Crosslinking Mass Spectrometry of Antibodies." In: *Antibody Structures*, Methods in Molecular Biology, Springer. *Accepted.*

Citation details (including a DOI for the software) will be added at the first release.

## Licence

MIT. See [LICENSE](LICENSE).

## Third-party software

DeltaXL uses PySide6 (LGPL) for its graphical interface.

## Author

Jens Hieronymus, University of Southern Denmark (Protein Research Group).
