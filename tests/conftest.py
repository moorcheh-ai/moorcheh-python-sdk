# tests/conftest.py

import pytest
import httpx
import os
from unittest.mock import patch # Use unittest.mock for patching os.environ

from moorcheh_sdk import MoorchehClient, AuthenticationError

# --- Constants (can also be defined here if shared) ---
DUMMY_API_KEY = "test_api_key_123"
DEFAULT_BASE_URL = "https://kj88v2w4p9.execute-api.us-east-2.amazonaws.com/v1"

# --- Shared Fixtures ---

@pytest.fixture(scope="function") # Default scope, explicitly stated for clarity
def mock_httpx_client(mocker):
    """
    Fixture to mock the internal httpx.Client used by MoorchehClient.
    Mocks the client instance and its 'request' and 'close' methods.
    """
    # Mock the httpx.Client class itself
    mock_client_class = mocker.patch('httpx.Client', autospec=True)

    # Configure the instance returned when httpx.Client() is called
    mock_instance = mock_client_class.return_value
    mock_instance.request = mocker.MagicMock(spec=httpx.Client.request)
    mock_instance.close = mocker.MagicMock(spec=httpx.Client.close)

    # Return the *mock instance* so tests can configure its behavior (e.g., request return value)
    # Although mocker provides access via mock_client_class.return_value, returning it explicitly can be clearer
    return mock_instance


@pytest.fixture(scope="function")
def client(mock_httpx_client):
    """
    Fixture to provide a MoorchehClient instance for testing.
    Initializes the client with a dummy API key and uses the mocked httpx client.
    Uses a context manager to ensure cleanup logic (__exit__) is triggered.
    """
    # Ensure the environment variable isn't interfering if not passed directly
    # Use patch.dict from unittest.mock for environment manipulation
    with patch.dict(os.environ, {}, clear=True):
        # Use the client's context manager to ensure __exit__ (and thus close) is handled
        with MoorchehClient(api_key=DUMMY_API_KEY) as client_instance:
             # The mock_httpx_client fixture already patched httpx.Client,
             # so this MoorchehClient will use the mock internally.
             # We can attach the mock instance to the client instance for easier access in tests if needed,
             # though accessing mock_httpx_client directly in the test function is standard.
             client_instance._mock_httpx_instance = mock_httpx_client
             yield client_instance # Provide the initialized client to the test

    # No explicit cleanup needed here, the context manager handles client.close(),
    # which calls mock_httpx_client.close()

@pytest.fixture(scope="function")
def client_no_env_key():
    """
    Fixture to set up the environment for testing client initialization
    when no API key is provided via constructor or environment variable.
    """
    # Ensure MOORCHEH_API_KEY is not set in the environment for this test
    with patch.dict(os.environ, {}, clear=True):
        yield # Allow the test that uses this fixture to run

    # Environment is automatically restored after 'yield' by patch.dict context manager

# --- Helper Functions (Optional - can also go here if shared) ---
# Example: If mock_response was needed in multiple test files, move it here.
# from unittest.mock import MagicMock
# def mock_response(mocker, status_code, json_data=None, text_data=None, content_type="application/json", headers=None):
#     """Helper to create a mock httpx.Response."""
#     # ... (implementation from test_client.py) ...
#     pass

