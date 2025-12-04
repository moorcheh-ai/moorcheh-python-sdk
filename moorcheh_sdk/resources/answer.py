import logging
from typing import Any

from ..exceptions import APIError, InvalidInputError
from .base import BaseResource

logger = logging.getLogger(__name__)


class Answer(BaseResource):
    def generate(
        self,
        namespace: str,
        query: str,
        top_k: int = 5,
        ai_model: str = "anthropic.claude-sonnet-4-20250514-v1:0",
        chat_history: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        Submits a query to a namespace and gets a generative AI answer.

        This endpoint performs a search, gathers the context, and sends it to a
        Large Language Model (LLM) to generate a conversational answer.

        Args:
            namespace: The single text-based namespace to search within.
            query: The user's question or prompt as a string.
            top_k: The number of search results to provide as context to the LLM
                (default: 5). Must be a positive integer.
            ai_model: The identifier for the LLM to use for generation
                (default: "anthropic.claude-v2:1").
            chat_history: An optional list of previous conversation turns to maintain
                context. Each item should be a dictionary. Defaults to None.
            temperature: The sampling temperature for the LLM, between 0 and 1.
                Higher values mean more randomness (default: 0.7).

        Returns:
            A dictionary containing the AI-generated answer and other metadata.
            Example:
            ```json
            {
              "answer": "AI-generated response text",
              "model": "anthropic.claude-v2:1",
              "contextCount": 3,
              "query": "your question here"
            }
            ```

        Raises:
            InvalidInputError: If `namespace` or `query` is invalid, or if other
                parameters are of the wrong type or out of range. Also raised
                for API 400 errors.
            NamespaceNotFound: If the specified `namespace` does not exist
                (API 404 error).
            AuthenticationError: If the API key is invalid or lacks permissions.
            APIError: For other unexpected API errors during the request.
            MoorchehError: For network issues or client-side request problems.
        """
        logger.info(
            "Attempting to get generative answer for query in namespace"
            f" '{namespace}'..."
        )

        if not namespace or not isinstance(namespace, str):
            raise InvalidInputError("'namespace' must be a non-empty string.")
        if not query or not isinstance(query, str):
            raise InvalidInputError("'query' must be a non-empty string.")
        if not isinstance(top_k, int) or top_k <= 0:
            raise InvalidInputError("'top_k' must be a positive integer.")
        if not isinstance(ai_model, str) or not ai_model:
            raise InvalidInputError("'ai_model' must be a non-empty string.")
        if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 1):
            raise InvalidInputError(
                "'temperature' must be a number between 0.0 and 1.0."
            )

        payload: dict[str, Any] = {
            "namespace": namespace,
            "query": query,
            "top_k": top_k,
            "type": "text",  # Hardcoded as per API design
            "aiModel": ai_model,
            "chatHistory": chat_history if chat_history is not None else [],
            "temperature": temperature,
        }
        logger.debug(f"Generative answer payload: {payload}")

        response_data = self._client._request(
            method="POST", endpoint="/answer", json_data=payload, expected_status=200
        )

        if not isinstance(response_data, dict):
            logger.error("Generative answer response was not a dictionary.")
            raise APIError(
                message="Unexpected response format from generative answer endpoint."
            )

        logger.info(
            "Successfully received generative answer. Model used:"
            f" {response_data.get('model')}"
        )
        return response_data
