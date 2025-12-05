import pytest

from moorcheh_sdk import MoorchehError


def test_retry_on_500(client, mocker, mock_response):
    """Test that the client retries on 500 errors."""
    # Mock responses: 500, 500, 200
    mock_resp_500 = mock_response(500, text_data="Internal Server Error")
    mock_resp_200 = mock_response(200, json_data={"namespaces": ["test-namespace"]})

    client._mock_httpx_instance.request.side_effect = [
        mock_resp_500,
        mock_resp_500,
        mock_resp_200,
    ]

    response = client.namespaces.list()

    assert client._mock_httpx_instance.request.call_count == 3
    assert response == {"namespaces": ["test-namespace"]}


def test_retry_max_retries_exceeded(client, mocker, mock_response):
    """Test that the client stops retrying after max_retries."""
    mock_resp_500 = mock_response(500, text_data="Internal Server Error")
    client._mock_httpx_instance.request.return_value = mock_resp_500

    # Default max_retries is 3
    with pytest.raises(MoorchehError):
        client.namespaces.list()

    # Initial call + 3 retries = 4 calls
    assert client._mock_httpx_instance.request.call_count == 4


def test_retry_on_429_with_retry_after(client, mocker, mock_response):
    """Test retry on 429 with Retry-After header."""
    mock_resp_429 = mock_response(429, text_data="Too Many Requests")
    mock_resp_429.headers["Retry-After"] = "0.1"
    mock_resp_200 = mock_response(200, json_data={"namespaces": ["test-namespace"]})

    client._mock_httpx_instance.request.side_effect = [mock_resp_429, mock_resp_200]

    response = client.namespaces.list()

    assert client._mock_httpx_instance.request.call_count == 2
    assert response == {"namespaces": ["test-namespace"]}


def test_no_retry_on_400(client, mocker, mock_response):
    """Test that 400 errors are NOT retried."""
    mock_resp_400 = mock_response(400, text_data="Bad Request")
    client._mock_httpx_instance.request.return_value = mock_resp_400

    from moorcheh_sdk import InvalidInputError

    with pytest.raises(InvalidInputError):
        client.namespaces.list()

    assert client._mock_httpx_instance.request.call_count == 1
