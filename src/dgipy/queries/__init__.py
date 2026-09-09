"""Provide queries and lazy accessors to queries.


Individual query loader classes provide ``gql`` queries via a ``.query`` property:

>>> from dgipy.queries import get_drugs
>>> get_drugs.query
DocumentNode at 0:545
"""

from importlib import resources

from gql import gql
from graphql import DocumentNode


class _LazyQueryLoader:
    """Provide lazy loading functionality for query access."""

    def __init__(self, query_name: str) -> None:
        self.query_name = query_name
        self._query = None

    @property
    def query(self) -> DocumentNode:
        if self._query is None:
            with resources.open_text(__name__, f"{self.query_name}.graphql") as f:
                self._query = gql(f.read())
        return self._query


get_all_genes = _LazyQueryLoader("get_all_genes")
get_all_drugs = _LazyQueryLoader("get_all_drugs")
get_drug_applications = _LazyQueryLoader("get_drug_applications")
get_drugs = _LazyQueryLoader("get_drugs")
get_gene_categories = _LazyQueryLoader("get_gene_categories")
get_genes = _LazyQueryLoader("get_genes")
get_interaction_types = _LazyQueryLoader("get_interaction_types")
get_interactions_by_drug = _LazyQueryLoader("get_interactions_by_drug")
get_interactions_by_gene = _LazyQueryLoader("get_interactions_by_gene")
get_sources = _LazyQueryLoader("get_sources")


__all__ = [
    "get_all_drugs",
    "get_all_genes",
    "get_drug_applications",
    "get_drugs",
    "get_gene_categories",
    "get_genes",
    "get_interaction_types",
    "get_interactions_by_drug",
    "get_interactions_by_gene",
    "get_sources",
]
