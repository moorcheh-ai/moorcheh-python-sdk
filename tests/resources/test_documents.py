import pytest

from moorcheh_sdk import (
    InvalidInputError,
    NamespaceNotFound,
)
from tests.constants import (
    TEST_DOC_ID_1,
    TEST_DOC_ID_2,
    TEST_NAMESPACE,
)


def test_upload_documents_success(client, mocker, mock_response):
    """Test successful queuing of documents for upload (202 Accepted)."""
    docs = [
        {"id": TEST_DOC_ID_1, "text": "First doc"},
        {"id": TEST_DOC_ID_2, "text": "Second doc"},
    ]
    expected_response = {
        "status": "queued",
        "submitted_ids": [TEST_DOC_ID_1, TEST_DOC_ID_2],
    }
    mock_resp = mock_response(202, json_data=expected_response)
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


def test_upload_documents_namespace_not_found(client, mocker, mock_response):
    """Test uploading documents to a non-existent namespace."""
    docs = [{"id": TEST_DOC_ID_1, "text": "Test"}]
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.documents.upload(namespace_name=TEST_NAMESPACE, documents=docs)
    client._mock_httpx_instance.request.assert_called_once()


def test_delete_documents_success_200(client, mocker, mock_response):
    """Test successful deletion of documents (200 OK)."""
    ids_to_delete = [TEST_DOC_ID_1, TEST_DOC_ID_2]
    expected_response = {
        "status": "success",
        "deleted_ids": ids_to_delete,
        "errors": [],
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.documents.delete(namespace_name=TEST_NAMESPACE, ids=ids_to_delete)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/documents/delete",
        json={"ids": ids_to_delete},
        params=None,
    )
    assert result == expected_response


def test_delete_documents_partial_success_207(client, mocker, mock_response):
    """Test partial deletion of documents (207 Multi-Status)."""
    ids_to_delete = [TEST_DOC_ID_1, "non-existent-id", TEST_DOC_ID_2]
    expected_response = {
        "status": "partial",
        "deleted_ids": [TEST_DOC_ID_1, TEST_DOC_ID_2],
        "errors": [{"id": "non-existent-id", "error": "ID not found"}],
    }
    mock_resp = mock_response(207, json_data=expected_response)
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


def test_delete_documents_namespace_not_found(client, mocker, mock_response):
    """Test deleting documents from a non-existent namespace."""
    ids = [TEST_DOC_ID_1]
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.documents.delete(namespace_name=TEST_NAMESPACE, ids=ids)
    client._mock_httpx_instance.request.assert_called_once()


def test_get_documents_success(client, mocker, mock_response):
    """Test successful retrieval of documents."""
    ids_to_get = [TEST_DOC_ID_1, TEST_DOC_ID_2]
    expected_response = {
        "documents": [
            {"id": TEST_DOC_ID_1, "text": "First doc", "metadata": {}},
            {"id": TEST_DOC_ID_2, "text": "Second doc", "metadata": {}},
        ]
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.documents.get(namespace_name=TEST_NAMESPACE, ids=ids_to_get)

    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST",
        url=f"/namespaces/{TEST_NAMESPACE}/documents/get",
        json={"ids": ids_to_get},
        params=None,
    )
    assert result == expected_response


@pytest.mark.parametrize(
    "invalid_ids", [None, [], ["id1", ""], ["id1", None], [123, {}], "not a list"]
)
def test_get_documents_invalid_input_client_side(client, invalid_ids):
    """Test client-side validation for get_documents IDs."""
    with pytest.raises(InvalidInputError):
        client.documents.get(namespace_name=TEST_NAMESPACE, ids=invalid_ids)
    client._mock_httpx_instance.request.assert_not_called()


def test_get_documents_namespace_not_found(client, mocker, mock_response):
    """Test getting documents from a non-existent namespace."""
    ids = [TEST_DOC_ID_1]
    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.documents.get(namespace_name=TEST_NAMESPACE, ids=ids)
    client._mock_httpx_instance.request.assert_called_once()
