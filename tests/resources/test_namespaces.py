import pytest

from moorcheh_sdk import (
    APIError,
    AuthenticationError,
    ConflictError,
    InvalidInputError,
    NamespaceNotFound,
)
from tests.constants import (
    TEST_NAMESPACE,
    TEST_VECTOR_DIM,
)


def test_create_namespace_success_text(client, mocker, mock_response):
    """Test successful creation of a text namespace."""
    mock_resp = mock_response(
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


def test_create_namespace_success_vector(client, mocker, mock_response):
    """Test successful creation of a vector namespace."""
    mock_resp = mock_response(
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


def test_create_namespace_conflict(client, mocker, mock_response):
    """Test creating a namespace that already exists (409 Conflict)."""
    error_text = f"Conflict: Namespace '{TEST_NAMESPACE}' already exists."
    mock_resp = mock_response(409, text_data=error_text)
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


def test_create_namespace_invalid_input_server_side(client, mocker, mock_response):
    """Test handling of 400 Bad Request from the server."""
    error_text = "Bad Request: Invalid characters in namespace name."
    mock_resp = mock_response(400, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(InvalidInputError, match=error_text):
        client.namespaces.create(namespace_name="invalid-name-$%^", type="text")
    client._mock_httpx_instance.request.assert_called_once()


def test_list_namespaces_success(client, mocker, mock_response):
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
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.namespaces.list()

    client._mock_httpx_instance.request.assert_called_once_with(
        method="GET", url="/namespaces", json=None, params=None
    )
    assert result == expected_response


def test_list_namespaces_success_empty(client, mocker, mock_response):
    """Test successfully listing when no namespaces exist."""
    expected_response = {"namespaces": [], "execution_time": 0.02}
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.namespaces.list()

    client._mock_httpx_instance.request.assert_called_once_with(
        method="GET", url="/namespaces", json=None, params=None
    )
    assert result == expected_response


def test_list_namespaces_api_error(client, mocker, mock_response):
    """Test handling of a 500 server error during list_namespaces."""
    mock_resp = mock_response(500, text_data="Internal Server Error")
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(APIError, match="API Error: Internal Server Error"):
        client.namespaces.list()
    client._mock_httpx_instance.request.assert_called_once()


def test_list_namespaces_auth_error(client, mocker, mock_response):
    """Test handling of a 401/403 error during list_namespaces."""
    error_text = "Forbidden/Unauthorized: Invalid API Key"
    mock_resp = mock_response(403, text_data="Invalid API Key")
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(AuthenticationError, match=error_text):
        client.namespaces.list()
    client._mock_httpx_instance.request.assert_called_once()


def test_list_namespaces_unexpected_format(client, mocker, mock_response):
    """Test handling of unexpected response format (e.g., not a dict)."""
    mock_resp = mock_response(200, text_data="Just a string response")  # Not JSON
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(APIError, match=r"Failed to decode JSON response.*"):
        client.namespaces.list()
    client._mock_httpx_instance.request.assert_called_once()


def test_list_namespaces_missing_key(client, mocker, mock_response):
    """Test handling of valid JSON but missing 'namespaces' key."""
    mock_resp = mock_response(
        200, json_data={"some_other_key": []}
    )  # Missing 'namespaces'
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(
        APIError,
        match="Invalid response structure: 'namespaces' key missing or not a list.",
    ):
        client.namespaces.list()
    client._mock_httpx_instance.request.assert_called_once()


def test_delete_namespace_success(client, mocker, mock_response):
    """Test successful deletion of a namespace (expecting 200 OK)."""
    # API returns 200 with a body now
    mock_resp = mock_response(
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


def test_delete_namespace_not_found(client, mocker, mock_response):
    """Test deleting a namespace that does not exist (404 Not Found)."""
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(404, text_data=error_text)
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
