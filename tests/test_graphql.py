from copy import deepcopy

import pytest
import requests_mock
from gql import gql

from dgipy.graphql import execute_paginated_query

QUERY = gql(
    """
    query getThings($after: String) {
      things(after: $after) {
        nodes { name }
        pageInfo { hasNextPage endCursor }
      }
    }
    """
)


def test_execute_paginated_query_collects_all_nodes():
    first_page = {
        "data": {
            "things": {
                "nodes": [{"name": "one"}],
                "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
            }
        }
    }
    last_page = {
        "data": {
            "things": {
                "nodes": [{"name": "two"}],
                "pageInfo": {"hasNextPage": False, "endCursor": "cursor-2"},
            }
        }
    }
    variables = {"filter": "value"}
    original_variables = deepcopy(variables)

    with requests_mock.Mocker() as mock:
        mock.post(
            "https://example.test/graphql",
            [{"json": first_page}, {"json": last_page}],
        )

        result = execute_paginated_query(
            QUERY, "things", variables, "https://example.test/graphql"
        )

        assert result == [{"name": "one"}, {"name": "two"}]
        assert variables == original_variables
        assert len(mock.request_history) == 2
        assert mock.request_history[0].json()["variables"] == {"filter": "value"}
        assert mock.request_history[1].json()["variables"] == {
            "filter": "value",
            "after": "cursor-1",
        }


def test_execute_paginated_query_accepts_response_without_page_info():
    with requests_mock.Mocker() as mock:
        mock.post(
            "https://example.test/graphql",
            json={"data": {"things": {"nodes": [{"name": "one"}]}}},
        )

        result = execute_paginated_query(
            QUERY, "things", api_url="https://example.test/graphql"
        )

    assert result == [{"name": "one"}]


@pytest.mark.parametrize("cursor", [None, "", "cursor-1"])
def test_execute_paginated_query_rejects_missing_or_repeated_cursor(cursor):
    responses = [
        {
            "json": {
                "data": {
                    "things": {
                        "nodes": [],
                        "pageInfo": {
                            "hasNextPage": True,
                            "endCursor": "cursor-1",
                        },
                    }
                }
            }
        },
        {
            "json": {
                "data": {
                    "things": {
                        "nodes": [],
                        "pageInfo": {"hasNextPage": True, "endCursor": cursor},
                    }
                }
            }
        },
    ]
    if cursor in (None, ""):
        responses = responses[1:]

    with requests_mock.Mocker() as mock:
        mock.post("https://example.test/graphql", responses)

        with pytest.raises(RuntimeError, match="did not provide a new end cursor"):
            execute_paginated_query(
                QUERY, "things", api_url="https://example.test/graphql"
            )
