from typing import Any, cast

from ..exceptions import APIError, InvalidInputError
from ..types import SearchResponse
from ..utils.logging import setup_logging
from .base import BaseResource

logger = setup_logging(__name__)


class Search(BaseResource):
    def query(
        self,
        namespaces: list[str],
        query: str | list[float],
        top_k: int = 10,
        threshold: float | None = 0.7,
        kiosk_mode: bool = False,
    ) -> SearchResponse:
        """
        Performs semantic search across namespaces.

        Args:
            namespaces: A list of namespace names to search within.
            query: The search query (text string or vector list).
            top_k: The maximum number of results to return. Defaults to 10.
            threshold: Minimum similarity score (0-1). Defaults to 0.7.
            kiosk_mode: Enable strict filtering. Defaults to False.

        Returns:
            A dictionary containing search results.

            Structure:
            {
                "results": [
                    {
                        "id": str | int,
                        "score": float,
                        "text": str,  # Only for text namespaces
                        "metadata": dict
                    }
                ],
                "execution_time": float
            }

        Raises:
            InvalidInputError: If input is invalid.
            NamespaceNotFound: If a namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        if not isinstance(namespaces, list) or not namespaces:
            raise InvalidInputError("'namespaces' must be a non-empty list of strings.")
        if not all(isinstance(ns, str) and ns for ns in namespaces):
            raise InvalidInputError(
                "All items in 'namespaces' list must be non-empty strings."
            )
        if not query:
            raise InvalidInputError("'query' cannot be empty.")
        if not isinstance(top_k, int) or top_k <= 0:
            raise InvalidInputError("'top_k' must be a positive integer.")
        if threshold is not None and (
            not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1)
        ):
            raise InvalidInputError(
                "'threshold' must be a number between 0 and 1, or None."
            )
        if not isinstance(kiosk_mode, bool):
            raise InvalidInputError("'kiosk_mode' must be a boolean.")

        query_type = "vector" if isinstance(query, list) else "text"
        logger.info(
            f"Attempting {query_type} search in namespace(s) '{', '.join(namespaces)}'"
            f" with top_k={top_k}, threshold={threshold}, kiosk={kiosk_mode}..."
        )

        payload: dict[str, Any] = {
            "namespaces": namespaces,
            "query": query,  # Keep original query type
            "top_k": top_k,
            "kiosk_mode": kiosk_mode,
        }
        if threshold is not None:
            payload["threshold"] = threshold

        logger.debug(
            f"Search payload: {payload}"
        )  # Be careful logging query if it could be sensitive/large

        response_data = self._client._request(
            method="POST", endpoint="/search", json_data=payload, expected_status=200
        )

        if not isinstance(response_data, dict):
            logger.error("Search response was not a dictionary.")
            raise APIError(message="Unexpected response format from search endpoint.")

        result_count = len(response_data.get("results", []))
        exec_time = response_data.get("execution_time", "N/A")
        logger.info(
            f"Search completed successfully. Found {result_count} result(s). Execution"
            f" time: {exec_time}s."
        )
        logger.debug(
            f"Search results: {response_data}"
        )  # Log full results at debug level
        return cast(SearchResponse, response_data)
