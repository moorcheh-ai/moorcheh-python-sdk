import pytest

from moorcheh_sdk import (
    InvalidInputError,
    NamespaceNotFound,
)
from tests.constants import (
    TEST_NAMESPACE,
    TEST_VEC_ID_1,
    TEST_VEC_ID_2,
    TEST_VECTOR_DIM,
)


def test_upload_vectors_success_201(client, mocker, mock_response):
    """Test successful upload of all vectors (201 Created)."""
    vectors = [
        {"id": TEST_VEC_ID_1, "vector": [0.1] * TEST_VECTOR_DIM, "metadata": {"k": "v"}}
    ]
    expected_response = {
        "status": "success",
        "vector_ids_processed": [TEST_VEC_ID_1],
        "errors": [],
    }
    mock_resp = mock_response(201, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.vectors.upload(namespace_name=TEST_NAMESPACE, vectors=vectors)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/vectors",
        json={"vectors": vectors},
        params=None,
    )
    assert result == expected_response


def test_upload_vectors_partial_success_207(client, mocker, mock_response):
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
    mock_resp = mock_response(207, json_data=expected_response)
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


def test_upload_vectors_namespace_not_found(client, mocker, mock_response):
    """Test uploading vectors to a non-existent namespace."""
    vectors = [{"id": TEST_VEC_ID_1, "vector": [0.1] * TEST_VECTOR_DIM}]
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.vectors.upload(namespace_name=TEST_NAMESPACE, vectors=vectors)
    client._mock_httpx_instance.request.assert_called_once()


def test_delete_vectors_success_200(client, mocker, mock_response):
    """Test successful deletion of vectors (200 OK)."""
    ids_to_delete = [TEST_VEC_ID_1, TEST_VEC_ID_2]
    expected_response = {
        "status": "success",
        "deleted_ids": ids_to_delete,
        "errors": [],
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.vectors.delete(namespace_name=TEST_NAMESPACE, ids=ids_to_delete)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/vectors/delete",
        json={"ids": ids_to_delete},
        params=None,
    )
    assert result == expected_response


def test_delete_vectors_partial_success_207(client, mocker, mock_response):
    """Test partial deletion of vectors (207 Multi-Status)."""
    ids_to_delete = [TEST_VEC_ID_1, "non-existent-id", TEST_VEC_ID_2]
    expected_response = {
        "status": "partial",
        "deleted_ids": [TEST_VEC_ID_1, TEST_VEC_ID_2],
        "errors": [{"id": "non-existent-id", "error": "ID not found"}],
    }
    mock_resp = mock_response(207, json_data=expected_response)
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


def test_delete_vectors_namespace_not_found(client, mocker, mock_response):
    """Test deleting vectors from a non-existent namespace."""
    ids = [TEST_VEC_ID_1]
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.vectors.delete(namespace_name=TEST_NAMESPACE, ids=ids)
    client._mock_httpx_instance.request.assert_called_once()
