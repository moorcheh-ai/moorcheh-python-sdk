import pytest

from moorcheh_sdk import (
    APIError,
    InvalidInputError,
)
from tests.constants import (
    TEST_NAMESPACE,
    TEST_NAMESPACE_2,
    TEST_VECTOR_DIM,
)


def test_search_success_text(client, mocker, mock_response):
    """Test successful text search."""
    query = "semantic search"
    namespaces = [TEST_NAMESPACE]
    top_k = 5
    expected_response = {
        "results": [
            {
                "id": "doc1",
                "score": 0.9,
                "text": "About semantic search...",
                "metadata": {},
            }
        ],
        "execution_time": 0.1,
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.similarity_search.query(
        namespaces=namespaces, query=query, top_k=top_k
    )

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url="/search",
        json={
            "namespaces": namespaces,
            "query": query,
            "top_k": top_k,
            "kiosk_mode": False,
            "threshold": 0.25,
        },
        params=None,
    )
    assert result == expected_response


def test_search_success_vector_with_threshold(client, mocker, mock_response):
    """Test successful vector search with threshold."""
    query = [0.1] * TEST_VECTOR_DIM
    namespaces = [TEST_NAMESPACE, TEST_NAMESPACE_2]
    top_k = 3
    threshold = 0.75
    expected_response = {
        "results": [{"id": "vec1", "score": 0.8, "metadata": {}}],
        "execution_time": 0.2,
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.similarity_search.query(
        namespaces=namespaces, query=query, top_k=top_k, threshold=threshold
    )

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url="/search",
        json={
            "namespaces": namespaces,
            "query": query,
            "top_k": top_k,
            "threshold": threshold,
            "kiosk_mode": False,
        },
        params=None,
    )
    assert result == expected_response


@pytest.mark.parametrize(
    "invalid_ns, invalid_query, invalid_k, invalid_thresh, invalid_kiosk",
    [
        ([], "q", 10, None, False),  # Empty namespaces
        (None, "q", 10, None, False),  # None namespaces
        (["ns1", ""], "q", 10, None, False),  # Empty string in namespaces
        (["ns1", 123], "q", 10, None, False),  # Non-string in namespaces
        (["ns1"], "", 10, None, False),  # Empty query
        (["ns1"], None, 10, None, False),  # None query
        (["ns1"], "q", 0, None, False),  # Zero top_k
        (["ns1"], "q", -1, None, False),  # Negative top_k
        (["ns1"], "q", "abc", None, False),  # Non-int top_k
        (["ns1"], "q", 10, 1.1, False),  # Threshold > 1
        (["ns1"], "q", 10, -0.1, False),  # Threshold < 0
        (["ns1"], "q", 10, "abc", False),  # Non-numeric threshold
        (["ns1"], "q", 10, None, "true"),  # Non-bool kiosk_mode
    ],
)
def test_search_invalid_input_client_side(
    client, invalid_ns, invalid_query, invalid_k, invalid_thresh, invalid_kiosk
):
    """Test client-side validation for search parameters."""
    with pytest.raises(InvalidInputError):
        client.similarity_search.query(
            namespaces=invalid_ns,
            query=invalid_query,
            top_k=invalid_k,
            threshold=invalid_thresh,
            kiosk_mode=invalid_kiosk,
        )
    client._mock_httpx_instance.request.assert_not_called()


def test_search_namespace_not_found(client, mocker, mock_response):
    """Test search with a non-existent namespace."""
    query = "test"
    namespaces = ["non-existent-ns"]
    error_text = "Namespace 'non-existent-ns' not found."
    mock_resp = mock_response(404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    """
    Note: The _request method maps 404 to NamespaceNotFound specifically for /namespaces/{name} endpoints.
    For /search, a 404 might indicate the endpoint itself is wrong, or the API might return 400/404 with specific messages.
    We'll test the NamespaceNotFound mapping here, assuming the API *could* return 404 this way,
    but also test 400 below. Adjust based on actual API behavior.
    """  # noqa: E501
    with pytest.raises(
        APIError, match="Not Found: Namespace 'non-existent-ns' not found."
    ):
        client.similarity_search.query(namespaces=namespaces, query=query)
    client._mock_httpx_instance.request.assert_called_once()


def test_search_invalid_input_server_side(client, mocker, mock_response):
    """Test search with invalid input rejected by server (400)."""
    query = "test"
    namespaces = [TEST_NAMESPACE]
    error_text = "Bad Request: Query type mismatch for namespace type."
    mock_resp = mock_response(400, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(InvalidInputError, match=error_text):
        client.similarity_search.query(namespaces=namespaces, query=query)
    client._mock_httpx_instance.request.assert_called_once()
