"""Provides methods for performing different searches in DGIdb"""

import logging
import os
from enum import Enum

import requests
from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from regbot.fetch.drugsfda import get_anda_results, get_nda_results

import dgipy.queries as queries

_logger = logging.getLogger(__name__)

API_ENDPOINT_URL = os.environ.get("DGIDB_API_URL", "https://dgidb.org/api/graphql")


_logger = logging.getLogger(__name__)


def _get_client(api_url: str) -> Client:
    """Acquire GraphQL client.

    :param api_url: endpoint to request data at
    :return: GraphQL client
    """
    transport = RequestsHTTPTransport(
        url=api_url, headers={"dgidb-client-name": "dgipy"}
    )
    return Client(transport=transport, fetch_schema_from_transport=True)


def _group_attributes(row: list[dict]) -> dict:
    grouped_dict = {}
    for attr in row:
        if attr["value"] is None:
            continue
        if attr["name"] in grouped_dict:
            grouped_dict[attr["name"]].append(attr["value"])
        else:
            grouped_dict[attr["name"]] = [attr["value"]]
    return grouped_dict


def _backfill_dicts(col: list[dict]) -> list[dict]:
    keys = {key for cell in col for key in cell}
    return [{key: cell.get(key) for key in keys} for cell in col]


def get_drugs(
    terms: list,
    immunotherapy: bool | None = None,
    antineoplastic: bool | None = None,
    api_url: str | None = None,
) -> dict:
    """Perform a record look up in DGIdb for a drug of interest

    :param terms: drugs for record lookup
    :param immunotherapy: filter option for results that are only immunotherapy
    :param antineoplastic: filter option for results that see antineoplastic use
    :param api_url: API endpoint for GraphQL request
    :return: drug data
    """
    params: dict[str, bool | list] = {"names": terms}
    if immunotherapy is not None:
        params["immunotherapy"] = immunotherapy
    if antineoplastic is not None:
        params["antineoplastic"] = antineoplastic

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    result = client.execute(queries.get_drugs.query, variable_values=params)

    output = {
        "drug_name": [],
        "drug_concept_id": [],
        "drug_aliases": [],
        "drug_attributes": [],
        "drug_is_antineoplastic": [],
        "drug_is_immunotherapy": [],
        "drug_is_approved": [],
        "drug_approval_ratings": [],
        "drug_fda_applications": [],
    }
    for match in result["drugs"]["nodes"]:
        output["drug_name"].append(match["name"])
        output["drug_concept_id"].append(match["conceptId"])
        output["drug_aliases"].append([a["alias"] for a in match["drugAliases"]])
        output["drug_attributes"].append(_group_attributes(match["drugAttributes"]))
        output["drug_is_antineoplastic"].append(match["antiNeoplastic"])
        output["drug_is_immunotherapy"].append(match["immunotherapy"])
        output["drug_is_approved"].append(match["approved"])
        output["drug_approval_ratings"].append(
            [
                {"rating": r["rating"], "source": r["source"]["sourceDbName"]}
                for r in match["drugApprovalRatings"]
            ]
        )
        output["drug_fda_applications"].append(
            [app["appNo"] for app in match["drugApplications"]]
        )
    output["drug_attributes"] = _backfill_dicts(output["drug_attributes"])
    return output


def get_genes(terms: list, api_url: str | None = None) -> dict:
    """Perform a record look up in DGIdb for genes of interest

    :param terms: genes for record lookup
    :param api_url: API endpoint for GraphQL request
    :return: gene data
    """
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    result = client.execute(queries.get_genes.query, variable_values={"names": terms})

    output = {
        "gene_name": [],
        "gene_concept_id": [],
        "gene_aliases": [],
        "gene_attributes": [],
    }
    for match in result["genes"]["nodes"]:
        output["gene_name"].append(match["name"])
        output["gene_concept_id"].append(match["conceptId"])
        output["gene_aliases"].append([a["alias"] for a in match["geneAliases"]])
        output["gene_attributes"].append(_group_attributes(match["geneAttributes"]))
    output["gene_attributes"] = _backfill_dicts(output["gene_attributes"])
    return output


def get_interactions(
    terms: list,
    search: str = "genes",
    immunotherapy: bool | None = None,
    antineoplastic: bool | None = None,
    source: str | None = None,
    pmid: int | None = None,
    interaction_type: str | None = None,
    approved: str | None = None,
    api_url: str | None = None,
) -> dict:
    """Perform an interaction look up for drugs or genes of interest

    :param terms: drugs or genes for interaction look up
    :param search: interaction search type. valid types are "drugs" or "genes"
    :param immunotherapy: filter option for results that are used in immunotherapy
    :param antineoplastic: filter option for results that are part of antineoplastic regimens
    :param source: filter option for specific database of interest
    :param pmid: filter option for specific PMID
    :param interaction_type: filter option for specific interaction types
    :param approved: filter option for approved interactions
    :param api_url: API endpoint for GraphQL request
    :return: interaction results for terms
    :raise ValueError: if invalid `search` arg used
    """
    params: dict[str, str | int | bool | list[str]] = {"names": terms}
    if immunotherapy is not None:
        params["immunotherapy"] = immunotherapy
    if antineoplastic is not None:
        params["antiNeoplastic"] = antineoplastic
    if source is not None:
        params["sourceDbName"] = source
    if pmid is not None:
        params["pmid"] = pmid
    if interaction_type is not None:
        params["interactionType"] = interaction_type
    if approved is not None:
        params["approved"] = approved

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)

    if search == "genes":
        raw_results = client.execute(
            queries.get_interactions_by_gene.query, variable_values=params
        )
        results = raw_results["genes"]["nodes"]
    elif search == "drugs":
        raw_results = client.execute(
            queries.get_interactions_by_drug.query, variable_values=params
        )
        results = raw_results["drugs"]["nodes"]
    else:
        msg = "Search type must be specified using: search='drugs' or search='genes'"
        raise ValueError(msg)
    output = {
        "gene_name": [],
        "gene_concept_id": [],
        "gene_long_name": [],
        "drug_name": [],
        "drug_concept_id": [],
        "drug_approved": [],
        "interaction_score": [],
        "interaction_attributes": [],
        "interaction_sources": [],
        "interaction_pmids": [],
    }
    for result in results:
        for interaction in result["interactions"]:
            output["gene_name"].append(interaction["gene"]["name"])
            output["gene_long_name"].append(interaction["gene"]["longName"])
            output["gene_concept_id"].append(interaction["gene"]["conceptId"])
            output["drug_name"].append(interaction["drug"]["name"])
            output["drug_concept_id"].append(interaction["drug"]["conceptId"])
            output["drug_approved"].append(interaction["drug"]["approved"])
            output["interaction_score"].append(interaction["interactionScore"])
            output["interaction_attributes"].append(
                _group_attributes(interaction["interactionAttributes"])
            )
            pubs = []
            sources = []
            for claim in interaction["interactionClaims"]:
                sources.append(claim["source"]["sourceDbName"])
                pubs += [p["pmid"] for p in claim["publications"]]
            output["interaction_pmids"].append(pubs)
            output["interaction_sources"].append(sources)
    output["interaction_attributes"] = _backfill_dicts(output["interaction_attributes"])
    return output


def get_categories(terms: list, api_url: str | None = None) -> dict:
    """Perform a category annotation lookup for genes of interest

    :param terms: Genes of interest for annotations
    :param api_url: API endpoint for GraphQL request
    :return: category annotation results for genes
    """
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    results = client.execute(
        queries.get_gene_categories.query, variable_values={"names": terms}
    )
    output = {
        "gene_name": [],
        "gene_concept_id": [],
        "gene_full_name": [],
        "gene_category": [],
        "gene_category_sources": [],
    }
    for result in results["genes"]["nodes"]:
        name = result["name"]
        long_name = result["longName"]
        concept_id = result["conceptId"]
        for cat in result["geneCategoriesWithSources"]:
            output["gene_name"].append(name)
            output["gene_concept_id"].append(concept_id)
            output["gene_full_name"].append(long_name)
            output["gene_category"].append(cat["name"])
            output["gene_category_sources"].append(cat["sourceNames"])
    return output


class SourceType(str, Enum):
    """Constrain source types for :py:method:`dgipy.dgidb.get_source` method."""

    DRUG = "drug"
    GENE = "gene"
    INTERACTION = "interaction"
    POTENTIALLY_DRUGGABLE = "potentially_druggable"


def get_sources(
    source_type: SourceType | None = None, api_url: str | None = None
) -> dict:
    """Perform a source lookup for relevant aggregate sources

    >>> from dgipy import get_source, SourceType
    >>> sources = get_source(SourceType.POTENTIALLY_DRUGGABLE)

    :param source_type: type of source to look up. Fetches all sources otherwise.
    :param api_url: API endpoint for GraphQL request
    :return: all sources of relevant type in a json object
    :raise TypeError: if invalid kind of data given as ``source_type`` param.
    """
    source_param = source_type.value.upper() if source_type is not None else None
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    params = {} if source_type is None else {"sourceType": source_param}
    results = client.execute(queries.get_sources.query, variable_values=params)
    output = {
        "source_name": [],
        "source_short_name": [],
        "source_version": [],
        "source_drug_claims": [],
        "source_gene_claims": [],
        "source_interaction_claims": [],
        "source_license": [],
        "source_license_url": [],
    }
    for result in results["sources"]["nodes"]:
        output["source_name"].append(result["fullName"])
        output["source_short_name"].append(result["sourceDbName"])
        output["source_version"].append(result["sourceDbVersion"])
        output["source_drug_claims"].append(result["drugClaimsCount"])
        output["source_gene_claims"].append(result["geneClaimsCount"])
        output["source_interaction_claims"].append(result["interactionClaimsCount"])
        output["source_license"].append(result["license"])
        output["source_license_url"].append(result["licenseLink"])
    return output


def get_all_genes(api_url: str | None = None) -> dict:
    """Get all gene names present in DGIdb

    :param api_url: API endpoint for GraphQL request
    :return: list of genes in DGIdb
    """
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    results = client.execute(queries.get_all_genes.query)
    genes = {"gene_name": [], "gene_concept_id": []}
    for result in results["genes"]["nodes"]:
        genes["gene_name"].append(result["name"])
        genes["gene_concept_id"].append(result["conceptId"])
    return genes


def get_all_drugs(api_url: str | None = None) -> dict:
    """Get all drug names present in DGIdb

    :param api_url: API endpoint for GraphQL request
    :return: a full list of drugs present in dgidb
    """
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    results = client.execute(queries.get_all_drugs.query)
    drugs = {"drug_name": [], "drug_concept_id": []}
    for result in results["drugs"]["nodes"]:
        drugs["drug_name"].append(result["name"])
        drugs["drug_concept_id"].append(result["conceptId"])
    return drugs


def get_drug_applications(terms: list, api_url: str | None = None) -> dict:
    """Perform a look up for ANDA/NDA applications for drug or drugs of interest

    :param terms: drugs of interest
    :param api_url: API endpoint for GraphQL request
    :return: all ANDA/NDA applications for drugs of interest
    """
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    results = client.execute(
        queries.get_drug_applications.query, variable_values={"names": terms}
    )
    output = {
        "drug_name": [],
        "drug_concept_id": [],
        "drug_product_application": [],
        "drug_brand_name": [],
        "drug_marketing_status": [],
        "drug_dosage_form": [],
        "drug_dosage_strength": [],
    }

    for result in results["drugs"]["nodes"]:
        name = result["name"]
        concept_id = result["conceptId"]
        for app in result["drugApplications"]:
            app_no = app["appNo"]
            anda = "anda" in app_no
            lui = app_no.split(":")[1]
            full_app_no = f"{'ANDA' if anda else 'NDA'}{lui}"
            try:
                if anda:
                    data = get_anda_results(lui, True)
                else:
                    data = get_nda_results(lui, True)
            except requests.exceptions.RequestException:
                _logger.warning(
                    "HTTP status error for Drugs@FDA lookup %s from drug %s: %s",
                    full_app_no,
                    concept_id,
                    name,
                )
                continue
            if not data:
                _logger.warning(
                    "No results for Drugs@FDA lookup %s from drug %s: %s",
                    full_app_no,
                    concept_id,
                    name,
                )
                continue
            for product in data[0].products:
                output["drug_name"].append(name)
                output["drug_concept_id"].append(concept_id)
                output["drug_product_application"].append(full_app_no)
                output["drug_brand_name"].append(product.brand_name)
                output["drug_marketing_status"].append(product.marketing_status)
                output["drug_dosage_form"].append(product.dosage_form)
                output["drug_dosage_strength"].append(
                    product.active_ingredients[0].strength
                )
    return output
