import os
from unittest.mock import patch

import httpx
import pytest

from moorcheh_sdk import (
    AuthenticationError,
    MoorchehClient,
    MoorchehError,
    __version__,
)
from tests.constants import (
    DEFAULT_BASE_URL,
    DUMMY_API_KEY,
)


def test_client_initialization_success_with_key(mock_httpx_client):
    """Test successful client initialization when API key is provided."""
    with patch.dict(os.environ, {}, clear=True):  # Isolate from env vars
        client_instance = MoorchehClient(
            api_key=DUMMY_API_KEY, base_url="http://test.url"
        )
        assert client_instance.api_key == DUMMY_API_KEY
        assert client_instance.base_url == "http://test.url"

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
        with MoorchehClient() as client_instance:
            assert client_instance.api_key == test_env_key
            assert client_instance.base_url == DEFAULT_BASE_URL
            httpx.Client.assert_called_once()
            call_args, call_kwargs = httpx.Client.call_args
            assert call_kwargs["headers"]["x-api-key"] == test_env_key


def test_client_initialization_failure_no_key(client_no_env_key):
    """Test client initialization fails if no API key is provided or found."""
    with pytest.raises(AuthenticationError, match="API key not provided"):
        MoorchehClient()


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


def test_request_timeout(client, mocker):
    """Test handling of httpx.TimeoutException."""
    client._mock_httpx_instance.request.side_effect = httpx.TimeoutException(
        "Request timed out", request=mocker.MagicMock()
    )

    with pytest.raises(MoorchehError, match="Request timed out after 30.0 seconds."):
        client.namespaces.list()
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


def test_client_context_manager(mock_httpx_client, mocker, mock_response):
    """Test that the client's close method is called when used as a context manager."""
    with patch.dict(os.environ, {}, clear=True):
        with MoorchehClient(api_key=DUMMY_API_KEY) as client_instance:
            assert isinstance(client_instance, MoorchehClient)
            mock_resp = mock_response(200, json_data={"namespaces": []})
            mock_httpx_client.request.return_value = mock_resp
            client_instance.namespaces.list()
        mock_httpx_client.close.assert_called_once()


def test_client_explicit_close(mock_httpx_client):
    """
    Test that calling client.close() explicitly calls the underlying client's close.
    """
    with patch.dict(os.environ, {}, clear=True):  # Isolate from env vars
        client_instance = MoorchehClient(api_key=DUMMY_API_KEY)
        client_instance.close()
        mock_httpx_client.close.assert_called_once()
