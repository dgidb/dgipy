from collections.abc import Callable
from io import StringIO
from pathlib import Path

import pytest
import requests_mock
from regbot.fetch.drugsfda import ProductDosageForm, ProductMarketingStatus

from dgipy.dgidb import (
    SourceType,
    get_all_genes,
    get_categories,
    get_drug_applications,
    get_drugs,
    get_genes,
    get_interactions,
    get_sources,
)


def test_get_drugs(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with (
        requests_mock.Mocker() as m,
        (fixtures_dir / "get_drug_api_response.json").open() as json_response,
        (
            fixtures_dir / "get_drug_filtered_api_response.json"
        ).open() as filtered_json_response,
    ):
        set_up_graphql_mock(m, json_response)

        results = get_drugs(["Imatinib"])
        assert len(results["drug_name"]), "DataFrame is non-empty"

        results_with_added_fake = get_drugs(["imatinib", "not-real"])
        assert len(results_with_added_fake["drug_name"]) == len(
            results["drug_name"]
        ), "Gracefully ignore non-existent search terms"

        # handling filters
        filtered_results = get_drugs(["imatinib", "metronidazole"], antineoplastic=True)
        assert len(filtered_results["drug_name"]) == 1, "Metronidazole is filtered out"
        assert (
            filtered_results["drug_name"][0] == "IMATINIB"
        ), "Imatinib is retained by the filter"
        assert all(results["drug_is_antineoplastic"]), "All results are antineoplastics"

        set_up_graphql_mock(m, filtered_json_response)
        filtered_results = get_drugs(
            ["imatinib", "metronidazole"], antineoplastic=False
        )
        assert len(filtered_results["drug_name"]), "DataFrame is non-empty"
        assert "METRONIDAZOLE" in filtered_results["drug_name"]

        # empty response
        set_up_graphql_mock(m, StringIO('{"data": {"drugs": {"nodes": []}}}'))
        empty_results = get_drugs(["not-real"])
        assert len(empty_results["drug_name"]) == 0, "Handles empty response"


def test_get_genes(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with (
        requests_mock.Mocker() as m,
        (fixtures_dir / "get_gene_api_response.json").open() as json_response,
    ):
        set_up_graphql_mock(m, json_response)

        results = get_genes(["ereg"])
        assert len(results["gene_name"]), "DataFrame is non-empty"

        results_with_added_fake = get_genes(["ereg", "not-real"])
        assert len(results_with_added_fake["gene_name"]) == len(
            results["gene_name"]
        ), "Gracefully ignore non-existent search terms"

        # empty response
        set_up_graphql_mock(m, StringIO('{"data": {"genes": {"nodes": []}}}'))
        empty_results = get_genes(["not-real"])
        assert len(empty_results["gene_name"]) == 0, "Handles empty response"


def test_get_interactions_by_genes(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with (
        requests_mock.Mocker() as m,
        (
            fixtures_dir / "get_interactions_by_genes_response.json"
        ).open() as genes_response,
        (
            fixtures_dir / "get_interactions_by_multiple_genes_response.json"
        ).open() as multiple_genes_response,
    ):
        set_up_graphql_mock(m, genes_response)
        results = get_interactions(["ereg"])
        assert len(results["gene_name"]), "Results are non-empty"

        results = get_interactions(["ereg", "not-real"])
        assert len(results["gene_name"]), "Handles additional not-real terms gracefully"

        # multiple terms
        set_up_graphql_mock(m, multiple_genes_response)
        multiple_gene_results = get_interactions(["ereg", "braf"])
        assert len(multiple_gene_results["gene_name"]) > len(
            results["gene_name"]
        ), "Handles multiple genes at once"

        # empty response
        set_up_graphql_mock(m, StringIO('{"data": {"genes": {"nodes": []}}}'))
        empty_results = get_interactions(["not-real"])
        assert len(empty_results["gene_name"]) == 0, "Handles empty response"


def test_get_interactions_by_gene_applies_drug_approval_and_source_filters(
    fixtures_dir: Path, set_up_graphql_mock: Callable
):
    """Gene searches must not expose records excluded by interaction filters.

    This response models the unfiltered KRAS results reported by the reviewer.
    Applying filters in dgiPy is important even when the upstream gene query
    does not apply them.
    """
    with (
        requests_mock.Mocker() as m,
        (
            fixtures_dir / "get_interactions_by_kras_unfiltered_response.json"
        ).open() as response,
    ):
        set_up_graphql_mock(m, response)
        results = get_interactions(["KRAS"], approved=True, source="ChEMBL")

    failures = []
    if not all(results["drug_approved"]):
        failures.append("unapproved drugs")
    if not all(
        source == "ChEMBL"
        for sources in results["interaction_sources"]
        for source in sources
    ):
        failures.append("interactions from other sources")

    assert not failures, f"Gene search returned {', '.join(failures)}"


def test_get_interactions_by_drugs(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with (
        requests_mock.Mocker() as m,
        (
            fixtures_dir / "get_interactions_by_drugs_response.json"
        ).open() as drugs_response,
        (
            fixtures_dir / "get_interactions_by_multiple_drugs_response.json"
        ).open() as multiple_drugs_response,
    ):
        set_up_graphql_mock(m, drugs_response)
        results = get_interactions(["sunitinib"], search="drugs")
        assert len(results["drug_name"]), "Results are non-empty"

        results = get_interactions(["sunitinib", "not-real"], search="drugs")
        assert len(results["drug_name"]), "Handles additional not-real terms gracefully"

        # multiple terms
        set_up_graphql_mock(m, multiple_drugs_response)
        multiple_gene_results = get_interactions(
            ["sunitinib", "clonazepam"], search="drugs"
        )
        assert len(multiple_gene_results["drug_name"]) > len(
            results["drug_name"]
        ), "Handles multiple drugs at once"

        # empty response
        set_up_graphql_mock(m, StringIO('{"data": {"drugs": {"nodes": []}}}'))
        empty_results = get_interactions(["not-real"], search="drugs")
        assert len(empty_results["drug_name"]) == 0, "Handles empty response"


def test_get_categories(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with (
        requests_mock.Mocker() as m,
        (fixtures_dir / "get_categories_response.json").open() as categories_response,
    ):
        set_up_graphql_mock(m, categories_response)
        results = get_categories(["BRAF"])
        assert len(results["gene_name"]), "Results are non-empty"
        assert "DRUG RESISTANCE" in results["gene_category"]
        assert "DRUGGABLE GENOME" in results["gene_category"]
        assert "CLINICALLY ACTIONABLE" in results["gene_category"]


def test_get_sources(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with (
        requests_mock.Mocker() as m,
        (fixtures_dir / "get_sources_response.json").open() as sources_response,
        (
            fixtures_dir / "get_sources_filtered_response.json"
        ).open() as filtered_sources_response,
    ):
        set_up_graphql_mock(m, sources_response)
        results = get_sources()
        assert (
            len(results["source_name"]) == 45
        ), f"Incorrect # of sources: {len(results['name'])}"

        set_up_graphql_mock(m, filtered_sources_response)
        results = get_sources(SourceType.GENE)
        sources = results["source_name"]
        assert len(sources) == 3, f"Incorrect # of sources: {len(sources)}"
        assert set(sources) == {
            "NCBI Gene",
            "HUGO Gene Nomenclature Committee",
            "Ensembl",
        }, "Contains correct sources"


def test_get_gene_list(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with (
        requests_mock.Mocker() as m,
        (
            fixtures_dir
            / "get_gene_list_response.json"  # this fixture is truncated from the real response
        ).open() as gene_list_response,
    ):
        set_up_graphql_mock(m, gene_list_response)

        results = get_all_genes()
        assert len(results["gene_name"]) == 9


def test_get_drug_applications(fixtures_dir, set_up_graphql_mock: Callable):
    with (
        requests_mock.Mocker() as m,
        (
            fixtures_dir / "get_drug_applications_response.json"
        ).open() as drug_applications_response,
        (
            fixtures_dir / "get_drug_applications_drugsatfda_response.json"
        ).open() as drugsatfda_response,
    ):
        set_up_graphql_mock(m, drug_applications_response)
        m.get(
            "https://api.fda.gov/drug/drugsfda.json?search=openfda.application_number:NDA212099&limit=500&skip=0",
            text=drugsatfda_response.read(),
        )
        results = get_drug_applications(["DAROLUTAMIDE"])
        assert len(results["drug_name"]) == 1
        assert results["drug_brand_name"][0] == "NUBEQA"
        assert results["drug_dosage_strength"][0] == "300MG"
        assert (
            results["drug_marketing_status"][0] == ProductMarketingStatus.PRESCRIPTION
        )
        assert results["drug_dosage_form"][0] == ProductDosageForm.TABLET


@pytest.mark.performance
def test_get_interactions_benchmark(benchmark):
    """Skipped by default -- call pytest with `--performance` flag to run.

    See `conftest.py` for details.
    """
    query = "braf"
    results = benchmark.pedantic(
        get_interactions,
        args=(query,),
        kwargs={"search": "genes"},
        rounds=10,
        warmup_rounds=0,
        iterations=1,
    )
    assert results.columns[0] == "gene"
