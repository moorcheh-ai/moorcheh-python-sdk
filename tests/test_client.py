# tests/test_client.py

import os
from unittest.mock import patch  # Use unittest.mock for patching os.environ

import httpx
import pytest

from moorcheh_sdk import (
    APIError,
    AuthenticationError,
    ConflictError,
    InvalidInputError,
    MoorchehClient,
    MoorchehError,
    NamespaceNotFound,
    __version__,
)

# --- Constants for Testing ---
DUMMY_API_KEY = "test_api_key_123"
DEFAULT_BASE_URL = "https://api.moorcheh.ai/v1"  # Match client default
TEST_NAMESPACE = "test-namespace"
TEST_NAMESPACE_2 = "another-namespace"
TEST_VECTOR_DIM = 10
TEST_DOC_ID_1 = "doc-abc"
TEST_DOC_ID_2 = 123  # Test integer ID
TEST_VEC_ID_1 = "vec-xyz"
TEST_VEC_ID_2 = 456  # Test integer ID
SDK_VERSION = "1.1.0"

# --- Fixtures ---


@pytest.fixture
def mock_httpx_client(mocker):
    """Fixture to mock the internal httpx.Client."""
    # Mock the httpx.Client instance created within MoorchehClient.__init__
    mock_client_instance = mocker.MagicMock(spec=httpx.Client)
    # Mock the request method on the instance
    mock_client_instance.request = mocker.MagicMock()
    # Mock the close method
    mock_client_instance.close = mocker.MagicMock()
    # Patch httpx.Client to return our mock instance when called
    mocker.patch("httpx.Client", return_value=mock_client_instance)
    return mock_client_instance


@pytest.fixture
def client(mock_httpx_client):
    """Fixture to provide a MoorchehClient instance with a mocked httpx client."""
    # Ensure the environment variable isn't interfering if not passed directly
    with patch.dict(os.environ, {}, clear=True):
        # Use context manager to ensure close is called if needed, though we mock it
        with MoorchehClient(api_key=DUMMY_API_KEY) as instance:
            # Attach the mock client instance for easier access in tests
            instance._mock_httpx_instance = mock_httpx_client
            yield instance  # Provide the instance to the test
    # __exit__ will call close on the client, which calls close on the mock


@pytest.fixture
def client_no_env_key(mock_httpx_client):
    """Fixture to test client initialization without API key."""
    # Ensure MOORCHEH_API_KEY is not set in the environment for this test
    with patch.dict(os.environ, {}, clear=True):
        yield  # Allow the test to run
    # Environment is restored automatically after 'yield'


def mock_response(
    mocker,
    status_code,
    json_data=None,
    text_data=None,
    content_type="application/json",
    headers=None,
):
    """Helper to create a mock httpx.Response."""
    response = mocker.MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.headers = headers or {"content-type": content_type}
    if json_data is not None:
        response.json.return_value = json_data
        # Simulate empty content if json_data is empty dict/list
        response.content = (
            b"{}"
            if isinstance(json_data, dict) and not json_data
            else (
                b"[]"
                if isinstance(json_data, list) and not json_data
                else b'{"data": "dummy"}'
            )
        )
    else:
        response.json.side_effect = Exception(
            "Cannot decode JSON"
        )  # Make sure .json() fails if no JSON
        response.content = b""  # Default empty content

    response.text = (
        text_data if text_data is not None else str(json_data) if json_data else ""
    )
    if response.content == b"" and response.text:
        response.content = response.text.encode("utf-8")

    # Mock raise_for_status to raise appropriate error only if status >= 400
    def raise_for_status_side_effect(*args, **kwargs):
        if status_code >= 400:
            raise httpx.HTTPStatusError(
                message=f"Mock Error {status_code}",
                request=mocker.MagicMock(),
                response=response,
            )

    response.raise_for_status = mocker.MagicMock(
        side_effect=raise_for_status_side_effect
    )

    return response


# --- Test Cases ---


# Test Client Initialization (__init__)
def test_client_initialization_success_with_key(mock_httpx_client):
    """Test successful client initialization when API key is provided."""
    with patch.dict(os.environ, {}, clear=True):  # Isolate from env vars
        client_instance = MoorchehClient(
            api_key=DUMMY_API_KEY, base_url="http://test.url"
        )
        assert client_instance.api_key == DUMMY_API_KEY
        assert client_instance.base_url == "http://test.url"
        # Check if httpx.Client was called correctly
        httpx.Client.assert_called_once_with(
            base_url="http://test.url",
            headers={
                "x-api-key": DUMMY_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"moorcheh-python-sdk/{__version__}",
            },
            timeout=30.0,  # Default timeout
        )
        client_instance.close()  # Explicitly close to avoid resource warnings


def test_client_initialization_success_with_env_var(mock_httpx_client):
    """Test successful client initialization using environment variable."""
    test_env_key = "key_from_env"
    with patch.dict(os.environ, {"MOORCHEH_API_KEY": test_env_key}, clear=True):
        with MoorchehClient() as client_instance:  # Use context manager
            assert client_instance.api_key == test_env_key
            assert client_instance.base_url == DEFAULT_BASE_URL  # Uses default URL
            httpx.Client.assert_called_once()  # Check it was called
            call_args, call_kwargs = httpx.Client.call_args
            assert call_kwargs["headers"]["x-api-key"] == test_env_key


def test_client_initialization_failure_no_key(client_no_env_key):
    """Test client initialization fails if no API key is provided or found."""
    with pytest.raises(AuthenticationError, match="API key not provided"):
        MoorchehClient()  # No key passed, env var cleared by fixture


def test_client_initialization_uses_env_base_url(mock_httpx_client):
    """Test client initialization uses MOORCHEH_BASE_URL environment variable."""
    test_env_url = "http://env.url"
    with patch.dict(
        os.environ,
        {"MOORCHEH_API_KEY": DUMMY_API_KEY, "MOORCHEH_BASE_URL": test_env_url},
        clear=True,
    ):
        with MoorchehClient() as client_instance:
            assert client_instance.base_url == test_env_url
            httpx.Client.assert_called_once()
            call_args, call_kwargs = httpx.Client.call_args
            assert call_kwargs["base_url"] == test_env_url


def test_client_initialization_base_url_priority(mock_httpx_client):
    """Test constructor base_url overrides environment variable."""
    constructor_url = "http://constructor.url"
    env_url = "http://env.url"
    with patch.dict(
        os.environ,
        {"MOORCHEH_API_KEY": DUMMY_API_KEY, "MOORCHEH_BASE_URL": env_url},
        clear=True,
    ):
        with MoorchehClient(base_url=constructor_url) as client_instance:
            assert client_instance.base_url == constructor_url  # Constructor wins
            httpx.Client.assert_called_once()
            call_args, call_kwargs = httpx.Client.call_args
            assert call_kwargs["base_url"] == constructor_url


# Test create_namespace
def test_create_namespace_success_text(client, mocker):
    """Test successful creation of a text namespace."""
    mock_resp = mock_response(
        mocker,
        201,
        json_data={
            "message": "Namespace created successfully",
            "namespace_name": TEST_NAMESPACE,
            "type": "text",
        },
    )
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.namespaces.create(namespace_name=TEST_NAMESPACE, type="text")

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url="/namespaces",
        json={
            "namespace_name": TEST_NAMESPACE,
            "type": "text",
            "vector_dimension": None,
        },
        params=None,
    )
    assert result == mock_resp.json.return_value


def test_create_namespace_success_vector(client, mocker):
    """Test successful creation of a vector namespace."""
    mock_resp = mock_response(
        mocker,
        201,
        json_data={
            "message": "Namespace created successfully",
            "namespace_name": TEST_NAMESPACE,
            "type": "vector",
            "vector_dimension": TEST_VECTOR_DIM,
        },
    )
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.namespaces.create(
        namespace_name=TEST_NAMESPACE, type="vector", vector_dimension=TEST_VECTOR_DIM
    )

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url="/namespaces",
        json={
            "namespace_name": TEST_NAMESPACE,
            "type": "vector",
            "vector_dimension": TEST_VECTOR_DIM,
        },
        params=None,
    )
    assert result == mock_resp.json.return_value


def test_create_namespace_conflict(client, mocker):
    """Test creating a namespace that already exists (409 Conflict)."""
    error_text = f"Conflict: Namespace '{TEST_NAMESPACE}' already exists."
    mock_resp = mock_response(mocker, 409, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(ConflictError, match=error_text):
        client.namespaces.create(namespace_name=TEST_NAMESPACE, type="text")
    client._mock_httpx_instance.request.assert_called_once()


@pytest.mark.parametrize(
    "name, ns_type, dim, expected_error_msg",
    [
        ("", "text", None, "'namespace_name' must be a non-empty string"),
        (None, "text", None, "'namespace_name' must be a non-empty string"),
        ("test", "invalid_type", None, "Namespace type must be 'text' or 'vector'"),
        (
            "test",
            "vector",
            None,
            "Vector dimension must be a positive integer for type 'vector'",
        ),
        (
            "test",
            "vector",
            0,
            "Vector dimension must be a positive integer for type 'vector'",
        ),
        (
            "test",
            "vector",
            -5,
            "Vector dimension must be a positive integer for type 'vector'",
        ),
        (
            "test",
            "vector",
            "abc",
            "Vector dimension must be a positive integer for type 'vector'",
        ),
        ("test", "text", 10, "Vector dimension should not be provided for type 'text'"),
    ],
)
def test_create_namespace_invalid_input_client_side(
    client, name, ns_type, dim, expected_error_msg
):
    """Test client-side validation for create_namespace."""
    with pytest.raises(InvalidInputError, match=expected_error_msg):
        client.namespaces.create(
            namespace_name=name, type=ns_type, vector_dimension=dim
        )
    client._mock_httpx_instance.request.assert_not_called()


def test_create_namespace_invalid_input_server_side(client, mocker):
    """Test handling of 400 Bad Request from the server."""
    error_text = "Bad Request: Invalid characters in namespace name."
    mock_resp = mock_response(mocker, 400, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(InvalidInputError, match=error_text):
        client.namespaces.create(namespace_name="invalid-name-$%^", type="text")
    client._mock_httpx_instance.request.assert_called_once()


# Test list_namespaces
def test_list_namespaces_success(client, mocker):
    """Test successfully listing namespaces."""
    expected_response = {
        "namespaces": [
            {"namespace_name": "ns1", "type": "text", "itemCount": 100},
            {
                "namespace_name": "ns2",
                "type": "vector",
                "itemCount": 500,
                "vector_dimension": 128,
            },
        ],
        "execution_time": 0.05,
    }
    mock_resp = mock_response(mocker, 200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.namespaces.list()

    client._mock_httpx_instance.request.assert_called_once_with(
        method="GET", url="/namespaces", json=None, params=None
    )
    assert result == expected_response


def test_list_namespaces_success_empty(client, mocker):
    """Test successfully listing when no namespaces exist."""
    expected_response = {"namespaces": [], "execution_time": 0.02}
    mock_resp = mock_response(mocker, 200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.namespaces.list()

    client._mock_httpx_instance.request.assert_called_once_with(
        method="GET", url="/namespaces", json=None, params=None
    )
    assert result == expected_response


def test_list_namespaces_api_error(client, mocker):
    """Test handling of a 500 server error during list_namespaces."""
    mock_resp = mock_response(mocker, 500, text_data="Internal Server Error")
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(APIError, match="API Error: Internal Server Error"):
        client.namespaces.list()
    client._mock_httpx_instance.request.assert_called_once()


def test_list_namespaces_auth_error(client, mocker):
    """Test handling of a 401/403 error during list_namespaces."""
    error_text = "Forbidden/Unauthorized: Invalid API Key"
    mock_resp = mock_response(mocker, 403, text_data="Invalid API Key")
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(AuthenticationError, match=error_text):
        client.namespaces.list()
    client._mock_httpx_instance.request.assert_called_once()


def test_list_namespaces_unexpected_format(client, mocker):
    """Test handling of unexpected response format (e.g., not a dict)."""
    mock_resp = mock_response(
        mocker, 200, text_data="Just a string response"
    )  # Not JSON
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(APIError, match=r"Failed to decode JSON response.*"):
        client.namespaces.list()
    client._mock_httpx_instance.request.assert_called_once()


def test_list_namespaces_missing_key(client, mocker):
    """Test handling of valid JSON but missing 'namespaces' key."""
    mock_resp = mock_response(
        mocker, 200, json_data={"some_other_key": []}
    )  # Missing 'namespaces'
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(
        APIError,
        match="Invalid response structure: 'namespaces' key missing or not a list.",
    ):
        client.namespaces.list()
    client._mock_httpx_instance.request.assert_called_once()


# Test delete_namespace
def test_delete_namespace_success(client, mocker):
    """Test successful deletion of a namespace (expecting 200 OK)."""
    # API returns 200 with a body now
    mock_resp = mock_response(
        mocker,
        200,
        json_data={"message": f"Namespace '{TEST_NAMESPACE}' deleted successfully."},
    )
    client._mock_httpx_instance.request.return_value = mock_resp

    # delete_namespace returns None on success
    result = client.namespaces.delete(TEST_NAMESPACE)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="DELETE", url=f"/namespaces/{TEST_NAMESPACE}", json=None, params=None
    )
    assert result is None  # Method returns None


def test_delete_namespace_not_found(client, mocker):
    """Test deleting a namespace that does not exist (404 Not Found)."""
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(mocker, 404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.namespaces.delete(TEST_NAMESPACE)
    client._mock_httpx_instance.request.assert_called_once()


@pytest.mark.parametrize("invalid_name", ["", None, 123])
def test_delete_namespace_invalid_name_client_side(client, invalid_name):
    """Test client-side validation for delete_namespace name."""
    with pytest.raises(
        InvalidInputError, match="'namespace_name' must be a non-empty string"
    ):
        client.namespaces.delete(invalid_name)
    client._mock_httpx_instance.request.assert_not_called()


# Test upload_documents
def test_upload_documents_success(client, mocker):
    """Test successful queuing of documents for upload (202 Accepted)."""
    docs = [
        {"id": TEST_DOC_ID_1, "text": "First doc"},
        {"id": TEST_DOC_ID_2, "text": "Second doc"},
    ]
    expected_response = {
        "status": "queued",
        "submitted_ids": [TEST_DOC_ID_1, TEST_DOC_ID_2],
    }
    mock_resp = mock_response(mocker, 202, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.documents.upload(namespace_name=TEST_NAMESPACE, documents=docs)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/documents",
        json={"documents": docs},
        params=None,
    )
    assert result == expected_response


@pytest.mark.parametrize(
    "invalid_docs",
    [
        None,
        [],
        [{"id": "d1"}],
        [{"text": "t1"}],
        [{"id": "", "text": "t1"}],
        [{"id": "d1", "text": ""}],
        [{"id": "d1", "text": "  "}],
        "not a list",
        [1, 2, 3],
        [{"id": "d1", "text": "t1"}, "string"],
    ],
)
def test_upload_documents_invalid_input_client_side(client, invalid_docs):
    """Test client-side validation for the documents payload."""
    with pytest.raises(InvalidInputError):  # Match specific message if needed
        client.documents.upload(namespace_name=TEST_NAMESPACE, documents=invalid_docs)
    client._mock_httpx_instance.request.assert_not_called()


def test_upload_documents_namespace_not_found(client, mocker):
    """Test uploading documents to a non-existent namespace."""
    docs = [{"id": TEST_DOC_ID_1, "text": "Test"}]
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(mocker, 404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.documents.upload(namespace_name=TEST_NAMESPACE, documents=docs)
    client._mock_httpx_instance.request.assert_called_once()


# Test upload_vectors
def test_upload_vectors_success_201(client, mocker):
    """Test successful upload of all vectors (201 Created)."""
    vectors = [
        {"id": TEST_VEC_ID_1, "vector": [0.1] * TEST_VECTOR_DIM, "metadata": {"k": "v"}}
    ]
    expected_response = {
        "status": "success",
        "vector_ids_processed": [TEST_VEC_ID_1],
        "errors": [],
    }
    mock_resp = mock_response(mocker, 201, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.vectors.upload(namespace_name=TEST_NAMESPACE, vectors=vectors)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/vectors",
        json={"vectors": vectors},
        params=None,
    )
    assert result == expected_response


def test_upload_vectors_partial_success_207(client, mocker):
    """Test partial success upload of vectors (207 Multi-Status)."""
    vectors = [
        {"id": TEST_VEC_ID_1, "vector": [0.1] * TEST_VECTOR_DIM},
        {
            "id": TEST_VEC_ID_2,
            "vector": [0.2] * (TEST_VECTOR_DIM + 1),
        },  # Mismatched dim
    ]
    expected_response = {
        "status": "partial",
        "vector_ids_processed": [TEST_VEC_ID_1],
        "errors": [{"id": TEST_VEC_ID_2, "error": "Vector dimension mismatch"}],
    }
    mock_resp = mock_response(mocker, 207, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.vectors.upload(namespace_name=TEST_NAMESPACE, vectors=vectors)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/vectors",
        json={"vectors": vectors},
        params=None,
    )
    assert result == expected_response


@pytest.mark.parametrize(
    "invalid_vectors",
    [
        None,
        [],
        [{"id": "v1"}],
        [{"vector": [0.1]}],
        [{"id": "", "vector": [0.1]}],
        [{"id": "v1", "vector": []}],
        [{"id": "v1", "vector": "not a list"}],
        "not a list",
        [1, 2, 3],
        [{"id": "v1", "vector": [0.1]}, "string"],
    ],
)
def test_upload_vectors_invalid_input_client_side(client, invalid_vectors):
    """Test client-side validation for the vectors payload."""
    with pytest.raises(InvalidInputError):
        client.vectors.upload(namespace_name=TEST_NAMESPACE, vectors=invalid_vectors)
    client._mock_httpx_instance.request.assert_not_called()


def test_upload_vectors_namespace_not_found(client, mocker):
    """Test uploading vectors to a non-existent namespace."""
    vectors = [{"id": TEST_VEC_ID_1, "vector": [0.1] * TEST_VECTOR_DIM}]
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(mocker, 404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.vectors.upload(namespace_name=TEST_NAMESPACE, vectors=vectors)
    client._mock_httpx_instance.request.assert_called_once()


# Test search
def test_search_success_text(client, mocker):
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
    mock_resp = mock_response(mocker, 200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.search.query(namespaces=namespaces, query=query, top_k=top_k)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url="/search",
        json={
            "namespaces": namespaces,
            "query": query,
            "top_k": top_k,
            "kiosk_mode": False,
        },
        params=None,
    )
    assert result == expected_response


def test_search_success_vector_with_threshold(client, mocker):
    """Test successful vector search with threshold."""
    query = [0.1] * TEST_VECTOR_DIM
    namespaces = [TEST_NAMESPACE, TEST_NAMESPACE_2]
    top_k = 3
    threshold = 0.75
    expected_response = {
        "results": [{"id": "vec1", "score": 0.8, "metadata": {}}],
        "execution_time": 0.2,
    }
    mock_resp = mock_response(mocker, 200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.search.query(
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
        client.search.query(
            namespaces=invalid_ns,
            query=invalid_query,
            top_k=invalid_k,
            threshold=invalid_thresh,
            kiosk_mode=invalid_kiosk,
        )
    client._mock_httpx_instance.request.assert_not_called()


def test_search_namespace_not_found(client, mocker):
    """Test search with a non-existent namespace."""
    query = "test"
    namespaces = ["non-existent-ns"]
    error_text = "Namespace 'non-existent-ns' not found."
    mock_resp = mock_response(mocker, 404, text_data=error_text)
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
        client.search.query(namespaces=namespaces, query=query)
    client._mock_httpx_instance.request.assert_called_once()


def test_search_invalid_input_server_side(client, mocker):
    """Test search with invalid input rejected by server (400)."""
    query = "test"
    namespaces = [TEST_NAMESPACE]
    error_text = "Bad Request: Query type mismatch for namespace type."
    mock_resp = mock_response(mocker, 400, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(InvalidInputError, match=error_text):
        client.search.query(namespaces=namespaces, query=query)
    client._mock_httpx_instance.request.assert_called_once()


# Test get_generative_answer
def test_get_generative_answer_success(client, mocker):
    """Test successful call to get_generative_answer."""
    query = "What is Moorcheh?"
    model = "anthropic.claude-v2:1"
    expected_response = {
        "answer": "Moorcheh is a semantic search engine.",
        "model": model,
        "contextCount": 3,
        "query": query,
    }
    mock_resp = mock_response(mocker, 200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.answer.generate(
        namespace=TEST_NAMESPACE, query=query, top_k=3, ai_model=model
    )

    expected_payload = {
        "namespace": TEST_NAMESPACE,
        "query": query,
        "top_k": 3,
        "type": "text",
        "aiModel": model,
        "chatHistory": [],
        "temperature": 0.7,
    }
    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST", url="/answer", json=expected_payload, params=None
    )
    assert result == expected_response


@pytest.mark.parametrize(
    "ns, q, tk, model, temp, history, msg",
    [
        ("", "q", 5, "m", 0.5, [], "'namespace' must be a non-empty string"),
        (None, "q", 5, "m", 0.5, [], "'namespace' must be a non-empty string"),
        ("ns", "", 5, "m", 0.5, [], "'query' must be a non-empty string"),
        ("ns", "q", 0, "m", 0.5, [], "'top_k' must be a positive integer"),
        ("ns", "q", -1, "m", 0.5, [], "'top_k' must be a positive integer"),
        ("ns", "q", 5, "", 0.5, [], "'ai_model' must be a non-empty string"),
        (
            "ns",
            "q",
            5,
            "m",
            1.1,
            [],
            "'temperature' must be a number between 0.0 and 1.0",
        ),
        (
            "ns",
            "q",
            5,
            "m",
            -0.1,
            [],
            "'temperature' must be a number between 0.0 and 1.0",
        ),
    ],
)
def test_get_generative_answer_invalid_input_client_side(
    client, ns, q, tk, model, temp, history, msg
):
    """Test client-side validation for get_generative_answer."""
    with pytest.raises(InvalidInputError, match=msg):
        client.answer.generate(
            namespace=ns,
            query=q,
            top_k=tk,
            ai_model=model,
            temperature=temp,
            chat_history=history,
        )
    client._mock_httpx_instance.request.assert_not_called()


def test_get_generative_answer_server_error(client, mocker):
    """Test get_generative_answer with a 500 server error."""
    mock_resp = mock_response(mocker, 500, text_data="Upstream LLM provider failed")
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(APIError, match="API Error: Upstream LLM provider failed"):
        client.answer.generate(namespace=TEST_NAMESPACE, query="test")
    client._mock_httpx_instance.request.assert_called_once()


# Test delete_documents
def test_delete_documents_success_200(client, mocker):
    """Test successful deletion of documents (200 OK)."""
    ids_to_delete = [TEST_DOC_ID_1, TEST_DOC_ID_2]
    expected_response = {
        "status": "success",
        "deleted_ids": ids_to_delete,
        "errors": [],
    }
    mock_resp = mock_response(mocker, 200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.documents.delete(namespace_name=TEST_NAMESPACE, ids=ids_to_delete)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/documents/delete",
        json={"ids": ids_to_delete},
        params=None,
    )
    assert result == expected_response


def test_delete_documents_partial_success_207(client, mocker):
    """Test partial deletion of documents (207 Multi-Status)."""
    ids_to_delete = [TEST_DOC_ID_1, "non-existent-id", TEST_DOC_ID_2]
    expected_response = {
        "status": "partial",
        "deleted_ids": [TEST_DOC_ID_1, TEST_DOC_ID_2],
        "errors": [{"id": "non-existent-id", "error": "ID not found"}],
    }
    mock_resp = mock_response(mocker, 207, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.documents.delete(namespace_name=TEST_NAMESPACE, ids=ids_to_delete)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/documents/delete",
        json={"ids": ids_to_delete},
        params=None,
    )
    assert result == expected_response


@pytest.mark.parametrize(
    "invalid_ids", [None, [], ["id1", ""], ["id1", None], [123, {}], "not a list"]
)
def test_delete_documents_invalid_input_client_side(client, invalid_ids):
    """Test client-side validation for delete_documents IDs."""
    with pytest.raises(InvalidInputError):
        client.documents.delete(namespace_name=TEST_NAMESPACE, ids=invalid_ids)
    client._mock_httpx_instance.request.assert_not_called()


def test_delete_documents_namespace_not_found(client, mocker):
    """Test deleting documents from a non-existent namespace."""
    ids = [TEST_DOC_ID_1]
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(mocker, 404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.documents.delete(namespace_name=TEST_NAMESPACE, ids=ids)
    client._mock_httpx_instance.request.assert_called_once()


# Test delete_vectors
def test_delete_vectors_success_200(client, mocker):
    """Test successful deletion of vectors (200 OK)."""
    ids_to_delete = [TEST_VEC_ID_1, TEST_VEC_ID_2]
    expected_response = {
        "status": "success",
        "deleted_ids": ids_to_delete,
        "errors": [],
    }
    mock_resp = mock_response(mocker, 200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.vectors.delete(namespace_name=TEST_NAMESPACE, ids=ids_to_delete)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/vectors/delete",
        json={"ids": ids_to_delete},
        params=None,
    )
    assert result == expected_response


def test_delete_vectors_partial_success_207(client, mocker):
    """Test partial deletion of vectors (207 Multi-Status)."""
    ids_to_delete = [TEST_VEC_ID_1, "non-existent-id", TEST_VEC_ID_2]
    expected_response = {
        "status": "partial",
        "deleted_ids": [TEST_VEC_ID_1, TEST_VEC_ID_2],
        "errors": [{"id": "non-existent-id", "error": "ID not found"}],
    }
    mock_resp = mock_response(mocker, 207, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.vectors.delete(namespace_name=TEST_NAMESPACE, ids=ids_to_delete)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/vectors/delete",
        json={"ids": ids_to_delete},
        params=None,
    )
    assert result == expected_response


@pytest.mark.parametrize(
    "invalid_ids", [None, [], ["id1", ""], ["id1", None], [123, {}], "not a list"]
)
def test_delete_vectors_invalid_input_client_side(client, invalid_ids):
    """Test client-side validation for delete_vectors IDs."""
    with pytest.raises(InvalidInputError):
        client.vectors.delete(namespace_name=TEST_NAMESPACE, ids=invalid_ids)
    client._mock_httpx_instance.request.assert_not_called()


def test_delete_vectors_namespace_not_found(client, mocker):
    """Test deleting vectors from a non-existent namespace."""
    ids = [TEST_VEC_ID_1]
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(mocker, 404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.vectors.delete(namespace_name=TEST_NAMESPACE, ids=ids)
    client._mock_httpx_instance.request.assert_called_once()


# Test _request method indirectly via other methods, but add specific error cases
def test_request_timeout(client, mocker):
    """Test handling of httpx.TimeoutException."""
    client._mock_httpx_instance.request.side_effect = httpx.TimeoutException(
        "Request timed out", request=mocker.MagicMock()
    )

    with pytest.raises(MoorchehError, match="Request timed out after 30.0 seconds."):
        client.namespaces.list()  # Any method that uses _request
    client._mock_httpx_instance.request.assert_called_once()


def test_request_network_error(client, mocker):
    """Test handling of httpx.RequestError."""
    error_msg = "Network error occurred"
    client._mock_httpx_instance.request.side_effect = httpx.RequestError(
        error_msg, request=mocker.MagicMock()
    )

    with pytest.raises(MoorchehError, match=f"Network or request error: {error_msg}"):
        client.namespaces.list()
    client._mock_httpx_instance.request.assert_called_once()


def test_request_unexpected_error(client, mocker):
    """Test handling of unexpected non-httpx errors during request."""
    error_msg = "Something completely unexpected happened"
    client._mock_httpx_instance.request.side_effect = ValueError(
        error_msg
    )  # Example unexpected error

    with pytest.raises(
        MoorchehError, match=f"An unexpected error occurred: {error_msg}"
    ):
        client.namespaces.list()
    client._mock_httpx_instance.request.assert_called_once()


# Test context manager usage ensures close is called
def test_client_context_manager(mock_httpx_client, mocker):
    """Test that the client's close method is called when used as a context manager."""
    with patch.dict(os.environ, {}, clear=True):  # Isolate from env vars
        with MoorchehClient(api_key=DUMMY_API_KEY) as client_instance:
            assert isinstance(client_instance, MoorchehClient)
            # Simulate doing something with the client if needed
            # Mock the response for list_namespaces to avoid APIError
            mock_resp = mock_response(mocker, 200, json_data={"namespaces": []})
            mock_httpx_client.request.return_value = mock_resp
            client_instance.namespaces.list()  # Call any method
        # After exiting the 'with' block,
        # close should have been called on the mock httpx instance
        mock_httpx_client.close.assert_called_once()


def test_client_explicit_close(mock_httpx_client):
    """
    Test that calling client.close() explicitly calls the underlying client's close.
    """
    with patch.dict(os.environ, {}, clear=True):  # Isolate from env vars
        client_instance = MoorchehClient(api_key=DUMMY_API_KEY)
        client_instance.close()
        mock_httpx_client.close.assert_called_once()
