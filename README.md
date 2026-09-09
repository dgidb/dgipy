# DGIpy

[![image](https://img.shields.io/pypi/v/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![image](https://img.shields.io/pypi/l/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![image](https://img.shields.io/pypi/pyversions/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![Actions status](https://github.com/genomicmedlab/dgipy/actions/workflows/checks.yaml/badge.svg)](https://github.com/genomicmedlab/dgipy/actions)

<!-- description -->
Python wrapper for querying a DGIdb v5 GraphQL API. DGIpy provides drug and gene
records, drug-gene interactions, gene categories, source metadata, and FDA drug
application information.
<!-- /description -->

## Installation

Install from [PyPI](https://pypi.org/project/dgipy/):

```shell
python3 -m pip install dgipy
```

## Usage

DGIpy is built around query functions that fetch data from the public DGIdb API.
Results use a column-oriented dictionary: each key is a column name and each value is
a list containing that column's values. The examples below show representative output;
the contents of the live DGIdb database may change.

```pycon
>>> from dgipy import get_genes
>>> results = get_genes(["BRAF"])
>>> results["gene_name"][0], results["gene_concept_id"][0], results["gene_aliases"][0][:5]
('BRAF', 'hgnc:1097', ['B-RAF PROTO-ONCOGENE, SERINE/THREONINE KINASE', 'BRAF1', 'BRAF-1', 'UCSC:UC003VWC.5', 'VEGA:OTTHUMG00000157457'])
```

This orientation enables easy use with the dataframe library of your choosing:

```pycon
>>> import pandas as pd
>>> pd.DataFrame(results)[["gene_name", "gene_concept_id"]]
  gene_name gene_concept_id
0      BRAF        hgnc:1097
>>>
>>> import polars as pl  # not included in DGIpy dependencies
>>> pl.DataFrame(results).select("gene_name", "gene_concept_id")
shape: (1, 2)
┌───────────┬─────────────────┐
│ gene_name ┆ gene_concept_id │
│ ---       ┆ ---             │
│ str       ┆ str             │
╞═══════════╪═════════════════╡
│ BRAF      ┆ hgnc:1097       │
└───────────┴─────────────────┘
```

### Available queries

| Function | Description |
| --- | --- |
| `get_drugs(terms, ...)` | Look up drug records by name. |
| `get_genes(terms, ...)` | Look up gene records by name. |
| `get_interactions(terms, ...)` | Find drug-gene interactions by gene or drug name. |
| `get_categories(terms, ...)` | Find category annotations for genes. |
| `get_sources(source_type=None, ...)` | List DGIdb source metadata, optionally filtered by `SourceType`. |
| `get_all_genes(...)` | List all gene names and concept identifiers. |
| `get_all_drugs(...)` | List all drug names and concept identifiers. Import this function from `dgipy.dgidb`. |
| `get_drug_applications(terms, ...)` | Combine DGIdb application identifiers with Drugs@FDA product data. |

The query functions accept an optional `api_url` argument when querying a DGIdb v5
instance other than the public endpoint:

```python
from dgipy import get_genes

genes = get_genes(["BRAF"], api_url="https://example.org/api/graphql")
```

## Development

Clone the repo and create a virtual environment:

```shell
git clone https://github.com/genomicmedlab/dgipy
cd dgipy
python3 -m virtualenv venv
source venv/bin/activate
```

Install development dependencies and `pre-commit`:

```shell
python3 -m pip install -e '.[dev,tests]'
pre-commit install
```

Check style with `ruff`:

```shell
python3 -m ruff format . && python3 -m ruff check --fix .
```

Run tests with `pytest`:

```shell
pytest
```
