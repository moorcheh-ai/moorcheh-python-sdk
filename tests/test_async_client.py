import tempfile
from pathlib import Path
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

    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": "test",
        "fileName": "test_document.pdf",
        "fileSize": len(test_file.read_bytes()),
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=200, json=lambda: expected_response
        )

        response = await client.documents.upload_file(
            namespace_name="test", file_path=str(test_file)
        )

        assert response == expected_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "POST"
        assert kwargs["path"] == "/namespaces/test/upload-file"
        assert "files" in kwargs


@pytest.mark.asyncio
async def test_upload_file_with_path_object(client, tmp_path):
    """Test async file upload using Path object."""
    test_file = tmp_path / "document.txt"
    test_file.write_text("Text content")

    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": "test",
        "fileName": "document.txt",
        "fileSize": len(test_file.read_bytes()),
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=200, json=lambda: expected_response
        )

        response = await client.documents.upload_file(
            namespace_name="test", file_path=test_file
        )

        assert response == expected_response
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_upload_file_with_file_like_object(client, tmp_path):
    """Test async file upload using file-like object."""
    test_file = tmp_path / "data.json"
    test_file.write_text('{"key": "value"}')

    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": "test",
        "fileName": "data.json",
        "fileSize": len(test_file.read_bytes()),
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=200, json=lambda: expected_response
        )

        with open(test_file, "rb") as f:
            response = await client.documents.upload_file(
                namespace_name="test", file_path=f
            )

        assert response == expected_response
        mock_request.assert_called_once()


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

    expected_response = {
        "success": True,
        "message": "File uploaded successfully",
        "namespace": "test",
        "fileName": f"test{file_extension}",
        "fileSize": len(test_file.read_bytes()),
    }

    with patch.object(client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = MagicMock(
            status_code=200, json=lambda: expected_response
        )

        response = await client.documents.upload_file(
            namespace_name="test", file_path=str(test_file)
        )

        assert response == expected_response
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_upload_file_too_large(client, tmp_path):
    """Test async file upload with file exceeding 10MB limit."""
    test_file = tmp_path / "large_file.pdf"
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    test_file.write_bytes(large_content)

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
