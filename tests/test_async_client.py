from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from moorcheh_sdk import AsyncMoorchehClient
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
            "top_k": 10,
            "ai_model": "gpt-4o",
            "temperature": 0.5,
        }
