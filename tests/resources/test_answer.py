import pytest

from moorcheh_sdk import (
    APIError,
    InvalidInputError,
)
from tests.constants import (
    TEST_NAMESPACE,
)


def test_get_generative_answer_success(client, mocker, mock_response):
    """Test successful call to get_generative_answer."""
    query = "What is Moorcheh?"
    model = "anthropic.claude-v2:1"
    expected_response = {
        "answer": "Moorcheh is a semantic search engine.",
        "model": model,
        "contextCount": 3,
        "query": query,
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    result = client.answer.generate(
        namespace=TEST_NAMESPACE, query=query, top_k=3, ai_model=model
    )

    expected_payload = {
        "namespace": TEST_NAMESPACE,
        "query": query,
        "top_k": 3,
        "type": "text",
        "aiModel": model,
        "chatHistory": [],
        "temperature": 0.7,
    }
    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST", url="/answer", json=expected_payload, params=None
    )
    assert result == expected_response


@pytest.mark.parametrize(
    "ns, q, tk, model, temp, history, msg",
    [
        ("", "q", 5, "m", 0.5, [], "'namespace' must be a non-empty string"),
        (None, "q", 5, "m", 0.5, [], "'namespace' must be a non-empty string"),
        ("ns", "", 5, "m", 0.5, [], "'query' must be a non-empty string"),
        ("ns", "q", 0, "m", 0.5, [], "'top_k' must be a positive integer"),
        ("ns", "q", -1, "m", 0.5, [], "'top_k' must be a positive integer"),
        ("ns", "q", 5, "", 0.5, [], "'ai_model' must be a non-empty string"),
        (
            "ns",
            "q",
            5,
            "m",
            1.1,
            [],
            "'temperature' must be a number between 0.0 and 1.0",
        ),
        (
            "ns",
            "q",
            5,
            "m",
            -0.1,
            [],
            "'temperature' must be a number between 0.0 and 1.0",
        ),
    ],
)
def test_get_generative_answer_invalid_input_client_side(
    client, ns, q, tk, model, temp, history, msg
):
    """Test client-side validation for get_generative_answer."""
    with pytest.raises(InvalidInputError, match=msg):
        client.answer.generate(
            namespace=ns,
            query=q,
            top_k=tk,
            ai_model=model,
            temperature=temp,
            chat_history=history,
        )
    client._mock_httpx_instance.request.assert_not_called()


def test_get_generative_answer_server_error(client, mocker, mock_response):
    """Test get_generative_answer with a 500 server error."""
    mock_resp = mock_response(500, text_data="Upstream LLM provider failed")
    client._mock_httpx_instance.request.return_value = mock_resp

    with pytest.raises(APIError, match="API Error: Upstream LLM provider failed"):
        client.answer.generate(namespace=TEST_NAMESPACE, query="test")
    client._mock_httpx_instance.request.assert_called_once()
