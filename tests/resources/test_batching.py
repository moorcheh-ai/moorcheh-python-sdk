from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from moorcheh_sdk import AsyncMoorchehClient, MoorchehClient


@pytest.fixture
def sync_client():
    return MoorchehClient(api_key="test")


@pytest.fixture
def async_client():
    return AsyncMoorchehClient(api_key="test")


def test_documents_upload_batching(sync_client):
    # Create 150 documents (should trigger 2 batches: 100 + 50)
    documents = [{"id": str(i), "text": f"doc {i}"} for i in range(150)]

    mock_response_1 = {
        "status": "queued",
        "submitted_ids": [str(i) for i in range(100)],
    }
    mock_response_2 = {
        "status": "queued",
        "submitted_ids": [str(i) for i in range(100, 150)],
    }

    with patch.object(sync_client, "request") as mock_request:
        mock_request.side_effect = [
            MagicMock(status_code=202, json=lambda: mock_response_1),
            MagicMock(status_code=202, json=lambda: mock_response_2),
        ]

        response = sync_client.documents.upload(
            namespace_name="test", documents=documents
        )

        assert response["status"] == "queued"
        assert len(response["submitted_ids"]) == 150
        assert mock_request.call_count == 2

        # Verify calls
        call_args_list = mock_request.call_args_list
        assert len(call_args_list[0].kwargs["json"]["documents"]) == 100
        assert len(call_args_list[1].kwargs["json"]["documents"]) == 50


@pytest.mark.asyncio
async def test_async_documents_upload_batching(async_client):
    documents = [{"id": str(i), "text": f"doc {i}"} for i in range(150)]

    mock_response_1 = {
        "status": "queued",
        "submitted_ids": [str(i) for i in range(100)],
    }
    mock_response_2 = {
        "status": "queued",
        "submitted_ids": [str(i) for i in range(100, 150)],
    }

    with patch.object(async_client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            MagicMock(status_code=202, json=lambda: mock_response_1),
            MagicMock(status_code=202, json=lambda: mock_response_2),
        ]

        response = await async_client.documents.upload(
            namespace_name="test", documents=documents
        )

        assert response["status"] == "queued"
        assert len(response["submitted_ids"]) == 150
        assert mock_request.call_count == 2


def test_vectors_upload_batching(sync_client):
    vectors = [{"id": str(i), "vector": [0.1] * 10} for i in range(150)]

    mock_response_1 = {
        "status": "success",
        "vector_ids_processed": [str(i) for i in range(100)],
        "errors": [],
    }
    mock_response_2 = {
        "status": "success",
        "vector_ids_processed": [str(i) for i in range(100, 150)],
        "errors": [],
    }

    with patch.object(sync_client, "request") as mock_request:
        mock_request.side_effect = [
            MagicMock(status_code=201, json=lambda: mock_response_1),
            MagicMock(status_code=201, json=lambda: mock_response_2),
        ]

        response = sync_client.vectors.upload(namespace_name="test", vectors=vectors)

        assert response["status"] == "success"
        assert len(response["vector_ids_processed"]) == 150
        assert len(response["errors"]) == 0
        assert mock_request.call_count == 2


@pytest.mark.asyncio
async def test_async_vectors_upload_batching(async_client):
    vectors = [{"id": str(i), "vector": [0.1] * 10} for i in range(150)]

    mock_response_1 = {
        "status": "success",
        "vector_ids_processed": [str(i) for i in range(100)],
        "errors": [],
    }
    mock_response_2 = {
        "status": "success",
        "vector_ids_processed": [str(i) for i in range(100, 150)],
        "errors": [],
    }

    with patch.object(async_client, "request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [
            MagicMock(status_code=201, json=lambda: mock_response_1),
            MagicMock(status_code=201, json=lambda: mock_response_2),
        ]

        response = await async_client.vectors.upload(
            namespace_name="test", vectors=vectors
        )

        assert response["status"] == "success"
        assert len(response["vector_ids_processed"]) == 150
        assert len(response["errors"]) == 0
        assert mock_request.call_count == 2
