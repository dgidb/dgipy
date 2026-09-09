# DGIpy

[![image](https://img.shields.io/pypi/v/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![image](https://img.shields.io/pypi/l/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![image](https://img.shields.io/pypi/pyversions/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![Actions status](https://github.com/genomicmedlab/dgipy/actions/workflows/checks.yaml/badge.svg)](https://github.com/genomicmedlab/dgipy/actions)

<!-- description -->
Python wrapper for accessing an instance of DGIdb v5 database. Currently supported searches will return individual interaction data for drugs or genes, category annotations for genes, or information for drugs.
<!-- /description -->

## Installation

Install from [PyPI](https://pypi.org/project/dgipy/):

```shell
python3 -m pip install dgipy
```

## Usage

DGIpy is built around query methods that wrap a GraphQL client and fetch data from the public DGIdb API endpoint. By default, data returned in a columnar format (i.e., as a dictionary where keys are column names and values are lists representing column data).

```pycon
>>> from dgipy import get_gene
>>> results = get_gene(["BRAF"])
>>> results["gene_name"][0], results["gene_concept_id"][0], results["gene_aliases"][0][:5]
('BRAF', 'hgnc:1097', ['B-RAF PROTO-ONCOGENE, SERINE/THREONINE KINASE', 'BRAF1', 'BRAF-1', 'UCSC:UC003VWC.5', 'VEGA:OTTHUMG00000157457'])
```

This orientation enables easy use within the dataframe library of your choosing:

```pycon
>>> import pandas as pd
>>> pd.DataFrame(results)
   name concept_id                                            aliases                                         attributes
0  BRAF  hgnc:1097  [B-RAF PROTO-ONCOGENE, SERINE/THREONINE KINASE...  {'BRAF MUT': ['Reported Genome Event Targeted'...
>>>
>>> import polars as pl  # not included in DGIpy dependencies
>>> pl.DataFrame(results)
shape: (1, 4)
┌──────┬────────────┬─────────────────────────────────┬─────────────────────────────────┐
│ name ┆ concept_id ┆ aliases                         ┆ attributes                      │
│ ---  ┆ ---        ┆ ---                             ┆ ---                             │
│ str  ┆ str        ┆ list[str]                       ┆ struct[14]                      │
╞══════╪════════════╪═════════════════════════════════╪═════════════════════════════════╡
│ BRAF ┆ hgnc:1097  ┆ ["B-RAF PROTO-ONCOGENE, SERINE… ┆ {["0"],["Swiss-Prot"],["Report… │
└──────┴────────────┴─────────────────────────────────┴─────────────────────────────────┘
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
