"""Execute GraphQL queries against the DGIdb API."""

import os
from collections.abc import Mapping
from typing import Any

from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from graphql import DocumentNode

API_ENDPOINT_URL = os.environ.get("DGIDB_API_URL", "https://dgidb.org/api/graphql")


def execute_paginated_query(
    query: DocumentNode,
    connection: str,
    variables: Mapping[str, Any] | None = None,
    api_url: str | None = None,
) -> list[dict[str, Any]]:
    """Execute a connection query and collect all of its nodes.

    Queries are expected to expose Relay-style ``nodes`` and ``pageInfo`` fields
    beneath ``connection``. A response without ``pageInfo`` is accepted as a
    single page for compatibility with older DGIdb instances.

    :param query: parsed GraphQL query document
    :param connection: top-level connection name in the query response
    :param variables: optional GraphQL variables; the mapping is not mutated
    :param api_url: GraphQL endpoint, defaulting to ``DGIDB_API_URL``
    :return: nodes collected from every response page
    :raises RuntimeError: if pagination cannot make forward progress
    """
    transport = RequestsHTTPTransport(
        url=api_url or API_ENDPOINT_URL,
        headers={"dgidb-client-name": "dgipy"},
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)
    request_variables = dict(variables or {})
    nodes: list[dict[str, Any]] = []
    initial_cursor = request_variables.get("after")
    seen_cursors = {initial_cursor} if isinstance(initial_cursor, str) else set()

    with client as session:
        while True:
            result = session.execute(query, variable_values=request_variables)
            page = result[connection]
            nodes.extend(page["nodes"])

            page_info = page.get("pageInfo")
            if not page_info or not page_info.get("hasNextPage"):
                return nodes

            cursor = page_info.get("endCursor")
            if not cursor or cursor in seen_cursors:
                msg = f"Pagination for {connection!r} did not provide a new end cursor"
                raise RuntimeError(msg)
            seen_cursors.add(cursor)
            request_variables["after"] = cursor
