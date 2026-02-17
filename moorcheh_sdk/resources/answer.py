from typing import Any, cast

from ..exceptions import APIError, InvalidInputError
from ..types import AnswerResponse, ChatHistoryItem
from ..utils.decorators import required_args
from ..utils.logging import setup_logging
from .base import AsyncBaseResource, BaseResource

logger = setup_logging(__name__)


class Answer(BaseResource):
    @required_args(["query"], types={"query": str})
    def generate(
        self,
        query: str,
        namespace: str | None = None,
        top_k: int | None = None,
        ai_model: str = "anthropic.claude-sonnet-4-20250514-v1:0",
        chat_history: list[ChatHistoryItem] | None = None,
        temperature: float = 0.7,
        header_prompt: str | None = None,
        footer_prompt: str | None = None,
        threshold: float | None = None,
        kiosk_mode: bool = False,
        structured_response: dict | None = None,
    ) -> AnswerResponse:
        """
        Generates an AI answer based on a search query within a namespace.

        This method performs a semantic search to retrieve relevant context and then
        uses a Large Language Model (LLM) to generate a conversational response.

        Args:
            query: The question or prompt to answer.
            namespace: The name of the text-based namespace to search within.
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
            threshold: Minimum similarity score (0-1) for search results when
                kiosk_mode is enabled. Defaults to 0.25.
            kiosk_mode: Enable strict filtering with threshold. Defaults to False.

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
        if namespace is None or not isinstance(namespace, str):
            raise InvalidInputError("Argument 'namespace' must be a string.")
        if namespace:
            if top_k is not None:
                if not isinstance(top_k, int) or top_k <= 0:
                    raise InvalidInputError("'top_k' must be a positive integer.")
            if threshold is not None:
                if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
                    raise InvalidInputError(
                        "'threshold' must be a number between 0 and 1, or None."
                    )
                if not kiosk_mode:
                    logger.warning(
                        "'threshold' is set but 'kiosk_mode' is disabled. 'threshold' will be ignored."
                    )
            logger.info(
                "Attempting to get generative answer for query in namespace"
                f" '{namespace}'..."
            )
        else:
            if top_k is not None:
                logger.warning(
                    "'top_k' was provided with an empty 'namespace' and will be ignored."
                )
            if kiosk_mode:
                logger.warning(
                    "'kiosk_mode' was enabled with an empty 'namespace' and will be ignored."
                )
            if threshold is not None:
                logger.warning(
                    "'threshold' was provided with an empty 'namespace' and will be ignored."
                )
            logger.info(
                "Attempting to get generative answer for query without namespace..."
            )
        if not ai_model:
            raise InvalidInputError("Argument 'ai_model' cannot be empty.")

        if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 2):
            raise InvalidInputError(
                "'temperature' must be a number between 0.0 and 2.0."
            )

        if structured_response is not None and not isinstance(
            structured_response, dict
        ):
            raise InvalidInputError("'structured_response' must be a dict or None.")

        payload: dict[str, Any] = {
            "namespace": namespace,
            "query": query,
            "aiModel": ai_model,
            "chatHistory": chat_history if chat_history is not None else [],
            "temperature": temperature,
            "headerPrompt": header_prompt if header_prompt is not None else "",
            "footerPrompt": footer_prompt if footer_prompt is not None else "",
        }
        if structured_response is not None:
            payload["structuredResponse"] = structured_response
        if namespace:
            payload["type"] = "text"  # Hardcoded as per API design
            payload["top_k"] = top_k if top_k is not None else 5
            payload["kiosk_mode"] = kiosk_mode
            if kiosk_mode:
                payload["threshold"] = threshold if threshold is not None else 0.25
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
    @required_args(["query"], types={"query": str})
    async def generate(
        self,
        query: str,
        namespace: str | None = None,
        top_k: int | None = None,
        ai_model: str = "anthropic.claude-sonnet-4-20250514-v1:0",
        chat_history: list[ChatHistoryItem] | None = None,
        temperature: float = 0.7,
        header_prompt: str | None = None,
        footer_prompt: str | None = None,
        threshold: float | None = None,
        kiosk_mode: bool = False,
        structured_response: dict | None = None,
    ) -> AnswerResponse:
        """
        Generates an AI answer based on a search query within a namespace asynchronously.

        This method performs a semantic search to retrieve relevant context and then
        uses a Large Language Model (LLM) to generate a conversational response.

        Args:
            query: The question or prompt to answer.
            namespace: The name of the text-based namespace to search within.
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
            threshold: Minimum similarity score (0-1) for search results when
                kiosk_mode is enabled. Defaults to 0.25.
            kiosk_mode: Enable strict filtering with threshold. Defaults to False.

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

        if namespace is None or not isinstance(namespace, str):
            raise InvalidInputError("Argument 'namespace' must be a string.")
        if namespace:
            if top_k is not None:
                if not isinstance(top_k, int) or top_k <= 0:
                    raise InvalidInputError("'top_k' must be a positive integer.")
            if threshold is not None:
                if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
                    raise InvalidInputError(
                        "'threshold' must be a number between 0 and 1, or None."
                    )
                if not kiosk_mode:
                    logger.warning(
                        "'threshold' is set but 'kiosk_mode' is disabled. 'threshold' will be ignored."
                    )
            logger.info(
                f"Attempting to generate answer for query '{query}' in namespace"
                f" '{namespace}' (model={ai_model})..."
            )
        else:
            if top_k is not None:
                logger.warning(
                    "'top_k' was provided with an empty 'namespace' and will be ignored."
                )
            if kiosk_mode:
                logger.warning(
                    "'kiosk_mode' was enabled with an empty 'namespace' and will be ignored."
                )
            if threshold is not None:
                logger.warning(
                    "'threshold' was provided with an empty 'namespace' and will be ignored."
                )
            logger.info(
                f"Attempting to generate answer for query '{query}' without namespace"
                f" (model={ai_model})..."
            )

        if not ai_model:
            raise InvalidInputError("Argument 'ai_model' cannot be empty.")
        if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 2):
            raise InvalidInputError("'temperature' must be between 0.0 and 2.0.")

        if structured_response is not None and not isinstance(
            structured_response, dict
        ):
            raise InvalidInputError("'structured_response' must be a dict or None.")

        payload: dict[str, Any] = {
            "namespace": namespace,
            "query": query,
            "aiModel": ai_model,
            "chatHistory": chat_history if chat_history is not None else [],
            "temperature": temperature,
            "headerPrompt": header_prompt if header_prompt is not None else "",
            "footerPrompt": footer_prompt if footer_prompt is not None else "",
        }
        if structured_response is not None:
            payload["structuredResponse"] = structured_response
        if namespace:
            payload["type"] = "text"  # Hardcoded as per API design
            payload["top_k"] = top_k if top_k is not None else 5
            payload["kiosk_mode"] = kiosk_mode
            if kiosk_mode:
                payload["threshold"] = threshold if threshold is not None else 0.25
        logger.debug(f"Generative answer payload: {payload}")

        response_data = await self._client._request(
            method="POST",
            endpoint="/answer",
            json_data=payload,
            expected_status=200,
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
