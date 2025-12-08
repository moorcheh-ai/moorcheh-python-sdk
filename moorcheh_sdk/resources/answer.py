from typing import Any, cast

from ..exceptions import APIError, InvalidInputError
from ..types import AnswerResponse, ChatHistoryItem
from ..utils.decorators import required_args
from ..utils.logging import setup_logging
from .base import AsyncBaseResource, BaseResource

logger = setup_logging(__name__)


class Answer(BaseResource):
    @required_args(
        ["namespace", "query", "top_k", "ai_model", "temperature"],
        types={
            "namespace": str,
            "query": str,
            "top_k": int,
            "ai_model": str,
            "temperature": (int, float),
        },
    )
    def generate(
        self,
        namespace: str,
        query: str,
        top_k: int = 5,
        ai_model: str = "anthropic.claude-sonnet-4-20250514-v1:0",
        chat_history: list[ChatHistoryItem] | None = None,
        temperature: float = 0.7,
        header_prompt: str | None = None,
        footer_prompt: str | None = None,
    ) -> AnswerResponse:
        """
        Generates an AI answer based on a search query within a namespace.

        This method performs a semantic search to retrieve relevant context and then
        uses a Large Language Model (LLM) to generate a conversational response.

        Args:
            namespace: The name of the text-based namespace to search within.
            query: The question or prompt to answer.
            top_k: The number of search results to use as context. Defaults to 5.
            ai_model: The identifier of the LLM to use.
                Defaults to "anthropic.claude-sonnet-4-20250514-v1:0".
            chat_history: Optional list of previous conversation turns for context.
                Each item should be a dictionary. Defaults to None.
            temperature: The sampling temperature for the LLM (0.0 to 1.0).
                Higher values introduce more randomness. Defaults to 0.7.
            header_prompt: Optional header prompt to be used in the LLM.
                Defaults to None.
            footer_prompt: Optional footer prompt to be used in the LLM.
                Defaults to None.

        Returns:
            A dictionary containing the generated answer and metadata.

            Structure:
            {
                "answer": str,
                "model": str,
                "contextCount": int,
                "query": str
            }

        Raises:
            InvalidInputError: If parameters are invalid (e.g., empty strings,
                negative numbers) or if the API returns a 400 Bad Request.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors (e.g., 500).
            MoorchehError: For network or connection issues.
        """
        logger.info(
            "Attempting to get generative answer for query in namespace"
            f" '{namespace}'..."
        )
        if top_k <= 0:
            raise InvalidInputError("'top_k' must be a positive integer.")
        if not (0 <= temperature <= 1):
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
            "headerPrompt": header_prompt if header_prompt is not None else "",
            "footerPrompt": footer_prompt if footer_prompt is not None else "",
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
            f"Answer generation completed successfully. Answer length: {len(response_data.get('answer', ''))}"
        )
        return cast(AnswerResponse, response_data)


class AsyncAnswer(AsyncBaseResource):
    @required_args(
        ["namespace", "query", "top_k", "ai_model", "temperature"],
        types={
            "namespace": str,
            "query": str,
            "top_k": int,
            "ai_model": str,
            "temperature": (int, float),
        },
    )
    async def generate(
        self,
        namespace: str,
        query: str,
        top_k: int = 10,
        ai_model: str = "anthropic.claude-sonnet-4-20250514-v1:0",
        temperature: float = 0.5,
    ) -> AnswerResponse:
        """
        Generates an answer to a query based on the content of a namespace asynchronously.

        Args:
            namespace: The name of the namespace to use as context.
            query: The question or query to answer.
            top_k: The number of relevant documents to retrieve for context (default: 10).
            ai_model: The AI model to use for generation (default: "gpt-4o").
            temperature: The creativity of the model (0.0 to 1.0, default: 0.5).

        Returns:
            A dictionary containing the generated answer and source documents.

            Structure:
            {
                "answer": str,
                "sources": [
                    {
                        "id": str | int,
                        "text": str,
                        "metadata": dict,
                        "score": float
                    }
                ],
                "execution_time": float
            }

        Raises:
            InvalidInputError: If input is invalid.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        if top_k <= 0:
            raise InvalidInputError("'top_k' must be a positive integer.")

        if not (0 <= temperature <= 1):
            raise InvalidInputError("'temperature' must be between 0.0 and 1.0.")

        logger.info(
            f"Attempting to generate answer for query '{query}' in namespace"
            f" '{namespace}' (model={ai_model})..."
        )

        payload = {
            "namespace": namespace,
            "query": query,
            "top_k": top_k,
            "ai_model": ai_model,
            "temperature": temperature,
        }

        response_data = await self._client._request(
            method="POST",
            endpoint="/answer",
            json_data=payload,
            expected_status=200,
        )

        if not isinstance(response_data, dict):
            logger.error("Answer response was not a dictionary.")
            raise APIError(message="Unexpected response format from answer endpoint.")

        logger.info(
            f"Answer generation completed successfully. Answer length: {len(response_data.get('answer', ''))}"
        )
        return cast(AnswerResponse, response_data)
