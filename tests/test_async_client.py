from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from moorcheh_sdk import (
    AsyncMoorchehClient,
    AuthenticationError,
    InvalidInputError,
    NamespaceNotFound,
)
from moorcheh_sdk.resources.answer import AsyncAnswer
from moorcheh_sdk.resources.documents import AsyncDocuments
from moorcheh_sdk.resources.namespaces import AsyncNamespaces
from moorcheh_sdk.resources.search import AsyncSearch
from moorcheh_sdk.resources.vectors import AsyncVectors


@pytest.fixture
def client():
    return AsyncMoorchehClient(api_key="test_key")


@pytest.mark.asyncio
async def test_client_initialization(client):
    assert client.api_key == "test_key"
    assert client.base_url == "https://api.moorcheh.ai/v1"
    assert isinstance(client.namespaces, AsyncNamespaces)
    assert isinstance(client.documents, AsyncDocuments)
    assert isinstance(client.vectors, AsyncVectors)
    assert isinstance(client.similarity_search, AsyncSearch)
    assert isinstance(client.answer, AsyncAnswer)


@pytest.mark.asyncio
async def test_namespaces_list(client):
    mock_response = {
        "namespaces": [
            {
                "namespace_name": "test",
                "type": "text",
                "itemCount": 0,
                "vector_dimension": None,
            }
        ],
        "execution_time": 0.1,
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=200, json=lambda: mock_response
        )

        response = await client.namespaces.list()

        assert response == mock_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "GET"
        assert kwargs["path"] == "/namespaces"


@pytest.mark.asyncio
async def test_documents_upload(client):
    documents = [{"id": "1", "text": "hello"}]
    mock_response = {"status": "queued", "submitted_ids": ["1"]}

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=202, json=lambda: mock_response
        )

        response = await client.documents.upload(
            namespace_name="test", documents=documents
        )

        assert response == mock_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "POST"
        assert kwargs["path"] == "/namespaces/test/documents"
        assert kwargs["json"] == {"documents": documents}


@pytest.mark.asyncio
async def test_search_query(client):
    mock_response = {"results": [], "execution_time": 0.1}

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=200, json=lambda: mock_response
        )

        response = await client.similarity_search.query(
            namespaces=["test"], query="hello"
        )

        assert response == mock_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "POST"
        assert kwargs["path"] == "/search"
        assert kwargs["json"] == {
            "namespaces": ["test"],
            "query": "hello",
            "top_k": 10,
            "kiosk_mode": False,
        }


@pytest.mark.asyncio
async def test_search_query_with_threshold(client):
    mock_response = {"results": [], "execution_time": 0.1}

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=200, json=lambda: mock_response
        )

        response = await client.similarity_search.query(
            namespaces=["test"], query="hello", threshold=0.5, kiosk_mode=True
        )

        assert response == mock_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["json"]["threshold"] == 0.5
        assert kwargs["json"]["kiosk_mode"] is True


@pytest.mark.asyncio
async def test_answer_generate(client):
    mock_response = {"answer": "world", "sources": [], "execution_time": 0.1}

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=200, json=lambda: mock_response
        )

        response = await client.answer.generate(namespace="test", query="hello")

        assert response == mock_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "POST"
        assert kwargs["path"] == "/answer"
        assert kwargs["json"] == {
            "namespace": "test",
            "query": "hello",
            "top_k": 5,
            "type": "text",
            "aiModel": "anthropic.claude-sonnet-4-20250514-v1:0",
            "chatHistory": [],
            "temperature": 0.7,
            "headerPrompt": "",
            "footerPrompt": "",
            "kiosk_mode": False,
        }


# File Upload Tests (Async)
@pytest.mark.asyncio
async def test_upload_file_success(client, tmp_path):
    """Test successful async file upload."""
    test_file = tmp_path / "test_document.pdf"
    test_file.write_bytes(b"PDF content here")

    upload_url_data = {
        "uploadUrl": "https://example.com/upload",
        "contentType": "application/pdf",
    }
    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": "test",
        "fileName": "test_document.pdf",
        "fileSize": len(test_file.read_bytes()),
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: upload_url_data,
                content=b"{}",
                headers={"content-type": "application/json"},
            ),
            MagicMock(status_code=200, text=""),
        ]

        response = await client.documents.upload_file(
            namespace_name="test", file_path=str(test_file)
        )

        assert response == expected_response
        assert mock_request.call_count == 2
        first_call = mock_request.call_args_list[0]
        assert first_call.kwargs["method"] == "POST"
        assert first_call.kwargs["path"] == "/namespaces/test/upload-url"
        assert first_call.kwargs["json"] == {"fileName": "test_document.pdf"}

        second_call = mock_request.call_args_list[1]
        assert second_call.kwargs["method"] == "PUT"
        assert second_call.kwargs["path"] == upload_url_data["uploadUrl"]



@pytest.mark.asyncio
async def test_upload_file_with_path_object(client, tmp_path):
    """Test async file upload using Path object."""
    test_file = tmp_path / "document.txt"
    test_file.write_text("Text content")

    upload_url_data = {
        "uploadUrl": "https://example.com/upload",
        "contentType": "text/plain",
    }
    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": "test",
        "fileName": "document.txt",
        "fileSize": len(test_file.read_bytes()),
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: upload_url_data,
                content=b"{}",
                headers={"content-type": "application/json"},
            ),
            MagicMock(status_code=200, text=""),
        ]

        response = await client.documents.upload_file(
            namespace_name="test", file_path=test_file
        )

        assert response == expected_response
        assert mock_request.call_count == 2


@pytest.mark.asyncio
async def test_upload_file_with_file_like_object(client, tmp_path):
    """Test async file upload using file-like object."""
    test_file = tmp_path / "data.json"
    test_file.write_text('{"key": "value"}')

    upload_url_data = {
        "uploadUrl": "https://example.com/upload",
        "contentType": "application/json",
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: upload_url_data,
                content=b"{}",
                headers={"content-type": "application/json"},
            ),
            MagicMock(status_code=200, text=""),
        ]

        with open(test_file, "rb") as f:
            expected_response = {
                "success": True,
                "message": "File uploaded successfully",
                "namespace": "test",
                "fileName": f.name,
                "fileSize": len(test_file.read_bytes()),
            }
            response = await client.documents.upload_file(
                namespace_name="test", file_path=f
            )

        assert response == expected_response
        assert mock_request.call_count == 2


@pytest.mark.asyncio
async def test_upload_file_not_found(client):
    """Test async file upload with non-existent file."""
    with pytest.raises(InvalidInputError, match="File not found"):
        await client.documents.upload_file(
            namespace_name="test", file_path="nonexistent.pdf"
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file_extension",
    [".exe", ".zip", ".jpg", ".png", ".mp4", ".py", ".js"],
)
async def test_upload_file_invalid_extension(client, tmp_path, file_extension):
    """Test async file upload with unsupported file extension."""
    test_file = tmp_path / f"test{file_extension}"
    test_file.write_bytes(b"content")

    with pytest.raises(InvalidInputError, match="is not supported"):
        await client.documents.upload_file(
            namespace_name="test", file_path=str(test_file)
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file_extension",
    [".pdf", ".docx", ".xlsx", ".json", ".txt", ".csv", ".md"],
)
async def test_upload_file_valid_extensions(client, tmp_path, file_extension):
    """Test async file upload with all valid file extensions."""
    test_file = tmp_path / f"test{file_extension}"
    test_file.write_bytes(b"content")

    upload_url_data = {
        "uploadUrl": "https://example.com/upload",
        "contentType": "application/json",
    }
    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": "test",
        "fileName": f"test{file_extension}",
        "fileSize": len(test_file.read_bytes()),
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: upload_url_data,
                content=b"{}",
                headers={"content-type": "application/json"},
            ),
            MagicMock(status_code=200, text=""),
        ]

        response = await client.documents.upload_file(
            namespace_name="test", file_path=str(test_file)
        )

        assert response == expected_response
        assert mock_request.call_count == 2


@pytest.mark.asyncio
async def test_upload_file_too_large(client, tmp_path):
    """Test async file upload with file exceeding 5GB limit."""
    # Create a file larger than 5GB
    test_file = tmp_path / "large_file.pdf"
    test_file.write_bytes(b"x")
    # Write 6GB of data
    too_large_size = 6 * 1024 * 1024 * 1024

    with patch("pathlib.Path.stat", return_value=MagicMock(st_size=too_large_size)):
        with pytest.raises(InvalidInputError, match="exceeds maximum allowed size"):
            await client.documents.upload_file(
                namespace_name="test", file_path=str(test_file)
            )


@pytest.mark.asyncio
async def test_upload_file_namespace_not_found(client, tmp_path):
    """Test async file upload to non-existent namespace."""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"content")

    error_text = "Namespace 'test' not found."

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 404
        mock_response_obj.text = error_text
        mock_response_obj.json.side_effect = Exception("Cannot decode JSON")
        mock_request.return_value = mock_response_obj

        with pytest.raises(NamespaceNotFound, match=error_text):
            await client.documents.upload_file(
                namespace_name="test", file_path=str(test_file)
            )
        mock_request.assert_called_once()
        assert mock_request.call_args.kwargs["path"] == "/namespaces/test/upload-url"


@pytest.mark.asyncio
async def test_upload_file_authentication_error(client, tmp_path):
    """Test async file upload with authentication error."""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"content")

    error_text = "Unauthorized: API key is required"

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 401
        mock_response_obj.text = error_text
        mock_response_obj.json.side_effect = Exception("Cannot decode JSON")
        mock_request.return_value = mock_response_obj

        with pytest.raises(AuthenticationError, match=error_text):
            await client.documents.upload_file(
                namespace_name="test", file_path=str(test_file)
            )
        mock_request.assert_called_once()
        assert mock_request.call_args.kwargs["path"] == "/namespaces/test/upload-url"


@pytest.mark.asyncio
async def test_upload_file_api_error(client, tmp_path):
    """Test async file upload with API error (500)."""
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"content")

    error_text = "Internal server error"

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        import httpx

        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 500
        mock_response_obj.text = error_text
        mock_response_obj.json.side_effect = Exception("Cannot decode JSON")
        # raise_for_status should raise httpx.HTTPStatusError
        mock_response_obj.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="HTTP 500",
            request=MagicMock(),
            response=mock_response_obj,
        )
        mock_request.return_value = mock_response_obj

        from moorcheh_sdk import APIError

        with pytest.raises(APIError, match=error_text):
            await client.documents.upload_file(
                namespace_name="test", file_path=str(test_file)
            )
        assert mock_request.call_args.kwargs["path"] == "/namespaces/test/upload-url"


@pytest.mark.asyncio
async def test_delete_files_success(client):
    """Test successful async deletion of files."""
    file_names = ["document.pdf", "report.docx"]
    expected_response = {
        "success": True,
        "message": "File deletion process completed.",
        "namespace": "test",
        "results": [
            {
                "fileName": file_names[0],
                "status": "deleted",
                "message": "File deletion initiated successfully",
            },
            {
                "fileName": file_names[1],
                "status": "deleted",
                "message": "File deletion initiated successfully",
            },
        ],
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=200, json=lambda: expected_response
        )

        response = await client.documents.delete_files(
            namespace_name="test", file_names=file_names
        )

        assert response == expected_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "DELETE"
        assert kwargs["path"] == "/namespaces/test/delete-file"
        assert kwargs["json"] == {"fileNames": file_names}


@pytest.mark.asyncio
async def test_delete_files_partial_success_207(client):
    """Test partial async deletion of files (207 Multi-Status)."""
    file_names = ["document.pdf", "missing.pdf"]
    expected_response = {
        "success": True,
        "message": "File deletion process completed.",
        "namespace": "test",
        "results": [
            {
                "fileName": file_names[0],
                "status": "deleted",
                "message": "File deletion initiated successfully",
            },
            {
                "fileName": file_names[1],
                "status": "not_found",
                "message": "File not found",
            },
        ],
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=207, json=lambda: expected_response
        )

        response = await client.documents.delete_files(
            namespace_name="test", file_names=file_names
        )

        assert response == expected_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "DELETE"
        assert kwargs["path"] == "/namespaces/test/delete-file"
        assert kwargs["json"] == {"fileNames": file_names}


@pytest.mark.parametrize(
    "invalid_file_names", [None, [], ["id1", ""], ["id1", None], [123, {}], "not a list"]
)
@pytest.mark.asyncio
async def test_delete_files_invalid_input_client_side(client, invalid_file_names):
    """Test client-side validation for async delete_files."""
    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        with pytest.raises(InvalidInputError):
            await client.documents.delete_files(
                namespace_name="test", file_names=invalid_file_names
            )
        mock_request.assert_not_called()


@pytest.mark.asyncio
async def test_delete_files_namespace_not_found(client):
    """Test async delete_files against a non-existent namespace."""
    file_names = ["document.pdf"]
    error_text = "Namespace 'test' not found."

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 404
        mock_response_obj.text = error_text
        mock_response_obj.json.side_effect = Exception("Cannot decode JSON")
        mock_request.return_value = mock_response_obj

        with pytest.raises(NamespaceNotFound, match=error_text):
            await client.documents.delete_files(
                namespace_name="test", file_names=file_names
            )
        mock_request.assert_called_once()
        assert mock_request.call_args.kwargs["path"] == "/namespaces/test/delete-file"
