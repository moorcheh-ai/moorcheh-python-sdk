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
        "headerPrompt": "",
        "footerPrompt": "",
        "kiosk_mode": False,
    }
    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST", url="/answer", json=expected_payload, params=None
    )
    assert result == expected_response


def test_generate_answer_with_prompts(client, mocker, mock_response):
    """Test get_generative_answer with header and footer prompts."""
    query = "What is Moorcheh?"
    header = "You are a helpful assistant."
    footer = "Answer concisely."

    expected_response = {
        "answer": "Moorcheh is great.",
        "model": "claude",
        "contextCount": 1,
        "query": query,
    }
    mock_resp = mock_response(200, json_data=expected_response)
    client._mock_httpx_instance.request.return_value = mock_resp

    client.answer.generate(
        namespace=TEST_NAMESPACE,
        query=query,
        header_prompt=header,
        footer_prompt=footer,
    )

    client._mock_httpx_instance.request.assert_called_once()
    call_args = client._mock_httpx_instance.request.call_args
    payload = call_args.kwargs["json"]

    assert payload["headerPrompt"] == header
    assert payload["footerPrompt"] == footer


@pytest.mark.parametrize(
    "ns, q, tk, model, temp, history, msg",
    [
        (None, "q", 5, "m", 0.5, [], "Argument 'namespace' must be a string."),
        ("ns", "", 5, "m", 0.5, [], "Argument 'query' cannot be empty."),
        ("ns", "q", 0, "m", 0.5, [], "'top_k' must be a positive integer"),
        ("ns", "q", -1, "m", 0.5, [], "'top_k' must be a positive integer"),
        ("ns", "q", 5, "", 0.5, [], "Argument 'ai_model' cannot be empty."),
        (
            "ns",
            "q",
            5,
            "m",
            2.1,
            [],
            "'temperature' must be a number between 0.0 and 2.0",
        ),
        (
            "ns",
            "q",
            5,
            "m",
            -0.1,
            [],
            "'temperature' must be a number between 0.0 and 2.0",
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
    assert client._mock_httpx_instance.request.call_count == 4


def test_empty_namespace(client, mocker, mock_response):
    """Test empty namespace to trigger direct AI mode."""
    query = "What is Moorcheh?"
    mock_resp = mock_response(
        200, json_data={"answer": "Moorcheh is a semantic search engine."}
    )
    client._mock_httpx_instance.request.return_value = mock_resp
    result = client.answer.generate(namespace="", query=query)
    expected_payload = {
        "namespace": "",
        "query": query,
        "aiModel": "anthropic.claude-sonnet-4-20250514-v1:0",
        "chatHistory": [],
        "temperature": 0.7,
        "headerPrompt": "",
        "footerPrompt": "",
    }
    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST", url="/answer", json=expected_payload, params=None
    )
    assert result["answer"] == "Moorcheh is a semantic search engine."


def test_structured_response(client, mocker, mock_response):
    """Test structured_response is accepted."""
    query = "What is Moorcheh?"
    structured = {"schema": {"type": "object"}}
    mock_resp = mock_response(
        200, json_data={"answer": "Moorcheh is a semantic search engine."}
    )
    client._mock_httpx_instance.request.return_value = mock_resp
    result = client.answer.generate(
        namespace="my_ns", query=query, structured_response=structured
    )
    expected_payload = {
        "namespace": "my_ns",
        "query": query,
        "aiModel": "anthropic.claude-sonnet-4-20250514-v1:0",
        "chatHistory": [],
        "temperature": 0.7,
        "headerPrompt": "",
        "footerPrompt": "",
        "type": "text",
        "top_k": 5,
        "kiosk_mode": False,
        "structuredResponse": structured,
    }
    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST", url="/answer", json=expected_payload, params=None
    )
    assert result["answer"] == "Moorcheh is a semantic search engine."


def test_structured_response_with_empty_namespace(client, mocker, mock_response):
    """Test structured_response is accepted and sent with empty namespace."""
    query = "What is Moorcheh?"
    structured = {"schema": {"type": "object"}}
    mock_resp = mock_response(
        200, json_data={"answer": "Moorcheh is a semantic search engine."}
    )
    client._mock_httpx_instance.request.return_value = mock_resp
    result = client.answer.generate(
        namespace="", query=query, structured_response=structured
    )
    expected_payload = {
        "namespace": "",
        "query": query,
        "aiModel": "anthropic.claude-sonnet-4-20250514-v1:0",
        "chatHistory": [],
        "temperature": 0.7,
        "headerPrompt": "",
        "footerPrompt": "",
        "structuredResponse": structured,
    }
    client._mock_httpx_instance.request.assert_called_once_with(
        method="POST", url="/answer", json=expected_payload, params=None
    )
    assert result["answer"] == "Moorcheh is a semantic search engine."


def test_structured_response_invalid_type(client):
    """Test structured_response not a dict raises InvalidInputError."""
    with pytest.raises(InvalidInputError, match="must be a dict or None"):
        client.answer.generate(
            namespace="", query="test", structured_response=[1, 2, 3]
        )
