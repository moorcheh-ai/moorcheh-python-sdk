import os
from unittest.mock import patch

import httpx
import pytest

from moorcheh_sdk import AsyncMoorchehClient
from tests.constants import DUMMY_API_KEY

# --- Async Fixtures ---


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
def mock_httpx_async_client(mocker):
    """Fixture to mock the internal httpx.AsyncClient."""
    mock_client_instance = mocker.MagicMock(spec=httpx.AsyncClient)
    mock_client_instance.request = mocker.AsyncMock()
    mock_client_instance.aclose = mocker.AsyncMock()
    mocker.patch("httpx.AsyncClient", return_value=mock_client_instance)
    return mock_client_instance


@pytest.fixture(scope="function")
async def async_client(mock_httpx_async_client):
    """Fixture to provide an AsyncMoorchehClient instance with a mocked httpx client."""
    with patch.dict(os.environ, {}, clear=True):
        async with AsyncMoorchehClient(api_key=DUMMY_API_KEY) as instance:
            instance._mock_httpx_instance = mock_httpx_async_client
            yield instance


@pytest.mark.anyio
async def test_async_client_initialization_success_with_key(mock_httpx_async_client):
    """Test successful async client initialization when API key is provided."""
    with patch.dict(os.environ, {}, clear=True):
        client_instance = AsyncMoorchehClient(
            api_key=DUMMY_API_KEY, base_url="http://test.url"
        )
        assert client_instance.api_key == DUMMY_API_KEY
        assert client_instance.base_url == "http://test.url"

        httpx.AsyncClient.assert_called_once()
        call_args, call_kwargs = httpx.AsyncClient.call_args
        assert call_kwargs["base_url"] == "http://test.url"
        assert call_kwargs["headers"]["x-api-key"] == DUMMY_API_KEY

        await client_instance.close()


@pytest.mark.anyio
async def test_async_client_context_manager(mock_httpx_async_client):
    """Test that the async client's close method is called when used as a context manager."""
    with patch.dict(os.environ, {}, clear=True):
        async with AsyncMoorchehClient(api_key=DUMMY_API_KEY) as client_instance:
            assert isinstance(client_instance, AsyncMoorchehClient)

        mock_httpx_async_client.aclose.assert_called_once()


@pytest.mark.anyio
async def test_async_request_success(async_client, mock_response):
    """Test a successful async request."""
    #     TODO: Implement async resources and methods.

    mock_resp = mock_response(200, json_data={"data": "success"})
    async_client._mock_httpx_instance.request.return_value = mock_resp

    response = await async_client.request("GET", "/test")

    assert response.status_code == 200
    assert response.json() == {"data": "success"}
    async_client._mock_httpx_instance.request.assert_called_once()
