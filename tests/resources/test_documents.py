import pytest

from moorcheh_sdk import (
    AuthenticationError,
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


# File Upload Tests
def test_upload_file_success(client, mocker, mock_response, tmp_path):
    """Test successful file upload."""
    # Create a temporary PDF file
    test_file = tmp_path / "test_document.pdf"
    test_file.write_bytes(b"PDF content here")

    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": TEST_NAMESPACE,
        "fileName": "test_document.pdf",
        "fileSize": len(test_file.read_bytes()),
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.documents.upload_file(
        namespace_name=TEST_NAMESPACE, file_path=str(test_file)
    )

    # Verify the request was made with files parameter
    # The request goes through client.request() which calls the base client's request
    # We need to check the actual httpx client's request call
    client._mock_httpx_instance.request.assert_called_once()
    call_args = client._mock_httpx_instance.request.call_args
    # httpx.Client.request is called with method, url, **kwargs
    assert call_args.kwargs["method"] == "POST"
    assert call_args.kwargs["url"] == f"/namespaces/{TEST_NAMESPACE}/upload-file"
    assert "files" in call_args.kwargs
    assert result == expected_response


def test_upload_file_with_path_object(client, mocker, mock_response, tmp_path):
    """Test file upload using Path object."""
    test_file = tmp_path / "document.txt"
    test_file.write_text("Text content")

    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": TEST_NAMESPACE,
        "fileName": "document.txt",
        "fileSize": len(test_file.read_bytes()),
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.documents.upload_file(
        namespace_name=TEST_NAMESPACE, file_path=test_file
    )

    assert result == expected_response
    client._mock_httpx_instance.request.assert_called_once()


def test_upload_file_with_file_like_object(client, mocker, mock_response, tmp_path):
    """Test file upload using file-like object."""
    test_file = tmp_path / "data.json"
    test_file.write_text('{"key": "value"}')

    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": TEST_NAMESPACE,
        "fileName": "data.json",
        "fileSize": len(test_file.read_bytes()),
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    with open(test_file, "rb") as f:
        result = client.documents.upload_file(
            namespace_name=TEST_NAMESPACE, file_path=f
        )

    assert result == expected_response
    client._mock_httpx_instance.request.assert_called_once()


def test_upload_file_not_found(client):
    """Test file upload with non-existent file."""
    with pytest.raises(InvalidInputError, match="File not found"):
        client.documents.upload_file(
            namespace_name=TEST_NAMESPACE, file_path="nonexistent.pdf"
        )
    client._mock_httpx_instance.request.assert_not_called()


@pytest.mark.parametrize(
    "file_extension",
    [".exe", ".zip", ".jpg", ".png", ".mp4", ".py", ".js"],
)
def test_upload_file_invalid_extension(client, tmp_path, file_extension):
    """Test file upload with unsupported file extension."""
    test_file = tmp_path / f"test{file_extension}"
    test_file.write_bytes(b"content")

    with pytest.raises(InvalidInputError, match="is not supported"):
        client.documents.upload_file(
            namespace_name=TEST_NAMESPACE, file_path=str(test_file)
        )
    client._mock_httpx_instance.request.assert_not_called()


@pytest.mark.parametrize(
    "file_extension",
    [".pdf", ".docx", ".xlsx", ".json", ".txt", ".csv", ".md"],
)
def test_upload_file_valid_extensions(
    client, mocker, mock_response, tmp_path, file_extension
):
    """Test file upload with all valid file extensions."""
    test_file = tmp_path / f"test{file_extension}"
    test_file.write_bytes(b"content")

    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": TEST_NAMESPACE,
        "fileName": f"test{file_extension}",
        "fileSize": len(test_file.read_bytes()),
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.documents.upload_file(
        namespace_name=TEST_NAMESPACE, file_path=str(test_file)
    )

    assert result == expected_response
    client._mock_httpx_instance.request.assert_called_once()


def test_upload_file_too_large(client, tmp_path):
    """Test file upload with file exceeding 10MB limit."""
    # Create a file larger than 10MB
    test_file = tmp_path / "large_file.pdf"
    # Write 11MB of data
    large_content = b"x" * (11 * 1024 * 1024)
    test_file.write_bytes(large_content)

    with pytest.raises(InvalidInputError, match="exceeds maximum allowed size"):
        client.documents.upload_file(
            namespace_name=TEST_NAMESPACE, file_path=str(test_file)
        )
    client._mock_httpx_instance.request.assert_not_called()


def test_upload_file_invalid_file_like_object(client):
    """Test file upload with invalid file-like object."""
    # A string that's not a valid file path will trigger "File not found" error
    with pytest.raises(InvalidInputError, match="File not found"):
        client.documents.upload_file(
            namespace_name=TEST_NAMESPACE, file_path="not a file"
        )
    client._mock_httpx_instance.request.assert_not_called()


def test_upload_file_invalid_file_like_object_type(client):
    """Test file upload with object that's not a file path or file-like."""
    # Pass an object that doesn't have a 'read' method and isn't a string/Path
    with pytest.raises(InvalidInputError, match="file path.*or a file-like object"):
        client.documents.upload_file(
            namespace_name=TEST_NAMESPACE,
            file_path=123,  # type: ignore
        )
    client._mock_httpx_instance.request.assert_not_called()


def test_upload_file_namespace_not_found(client, mocker, mock_response, tmp_path):
    """Test file upload to non-existent namespace."""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"content")

    error_text = f"Namespace '{TEST_NAMESPACE}' not found."
    mock_resp = mock_response(404, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(NamespaceNotFound, match=error_text):
        client.documents.upload_file(
            namespace_name=TEST_NAMESPACE, file_path=str(test_file)
        )
    client._mock_httpx_instance.request.assert_called_once()


def test_upload_file_authentication_error(client, mocker, mock_response, tmp_path):
    """Test file upload with authentication error."""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"content")

    error_text = "Unauthorized: API key is required"
    mock_resp = mock_response(401, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(AuthenticationError, match=error_text):
        client.documents.upload_file(
            namespace_name=TEST_NAMESPACE, file_path=str(test_file)
        )
    client._mock_httpx_instance.request.assert_called_once()


def test_upload_file_api_error(client, mocker, mock_response, tmp_path):
    """Test file upload with API error (500)."""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"content")

    error_text = "Internal server error"
    mock_resp = mock_response(500, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    from moorcheh_sdk import APIError

    with pytest.raises(APIError, match=error_text):
        client.documents.upload_file(
            namespace_name=TEST_NAMESPACE, file_path=str(test_file)
        )
    # The client retries on 500 errors, so it will be called multiple times
    assert client._mock_httpx_instance.request.call_count >= 1


def test_upload_file_invalid_input_error(client, mocker, mock_response, tmp_path):
    """Test file upload with API returning 400 Bad Request."""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"content")

    error_text = "No file was uploaded"
    mock_resp = mock_response(400, text_data=error_text)
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(InvalidInputError, match=error_text):
        client.documents.upload_file(
            namespace_name=TEST_NAMESPACE, file_path=str(test_file)
        )
    client._mock_httpx_instance.request.assert_called_once()
