import os
from unittest.mock import patch  # Use unittest.mock for patching os.environ

import httpx
import pytest

from moorcheh_sdk import MoorchehClient
from tests.constants import DUMMY_API_KEY

# --- Shared Fixtures ---


@pytest.fixture(scope="function")
def mock_httpx_client(mocker):
    """Fixture to mock the internal httpx.Client."""
    # Mock the httpx.Client instance created within MoorchehClient.__init__
    mock_client_instance = mocker.MagicMock(spec=httpx.Client)
    # Mock the request method on the instance
    mock_client_instance.request = mocker.MagicMock()
    # Mock the close method
    mock_client_instance.close = mocker.MagicMock()
    # Patch httpx.Client to return our mock instance when called
    mocker.patch("httpx.Client", return_value=mock_client_instance)
    return mock_client_instance


@pytest.fixture(scope="function")
def client(mock_httpx_client):
    """Fixture to provide a MoorchehClient instance with a mocked httpx client."""
    # Ensure the environment variable isn't interfering if not passed directly
    with patch.dict(os.environ, {}, clear=True):
        # Use context manager to ensure close is called if needed, though we mock it
        with MoorchehClient(api_key=DUMMY_API_KEY) as instance:
            # Attach the mock client instance for easier access in tests
            instance._mock_httpx_instance = mock_httpx_client
            yield instance  # Provide the instance to the test
    # __exit__ will call close on the client, which calls close on the mock


@pytest.fixture(scope="function")
def client_no_env_key():
    """Fixture to test client initialization without API key."""
    # Ensure MOORCHEH_API_KEY is not set in the environment for this test
    with patch.dict(os.environ, {}, clear=True):
        yield  # Allow the test to run
    # Environment is restored automatically after 'yield'


@pytest.fixture
def mock_response(mocker):
    """Helper to create a mock httpx.Response."""

    def _mock_response(
        status_code,
        json_data=None,
        text_data=None,
        content_type="application/json",
        headers=None,
    ):
        response = mocker.MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.headers = headers or {"content-type": content_type}
        if json_data is not None:
            response.json.return_value = json_data
            # Simulate empty content if json_data is empty dict/list
            response.content = (
                b"{}"
                if isinstance(json_data, dict) and not json_data
                else (
                    b"[]"
                    if isinstance(json_data, list) and not json_data
                    else b'{"data": "dummy"}'
                )
            )
        else:
            response.json.side_effect = Exception(
                "Cannot decode JSON"
            )  # Make sure .json() fails if no JSON
            response.content = b""  # Default empty content

        response.text = (
            text_data if text_data is not None else str(json_data) if json_data else ""
        )
        if response.content == b"" and response.text:
            response.content = response.text.encode("utf-8")

        # Mock raise_for_status to raise appropriate error only if status >= 400
        def raise_for_status_side_effect(*args, **kwargs):
            if status_code >= 400:
                raise httpx.HTTPStatusError(
                    message=f"Mock Error {status_code}",
                    request=mocker.MagicMock(),
                    response=response,
                )

        response.raise_for_status = mocker.MagicMock(
            side_effect=raise_for_status_side_effect
        )

        return response

    return _mock_response
