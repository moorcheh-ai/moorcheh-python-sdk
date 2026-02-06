from typing import Any, cast

from ..exceptions import APIError, InvalidInputError
from ..types import SearchResponse
from ..utils.decorators import required_args
from ..utils.logging import setup_logging
from .base import AsyncBaseResource, BaseResource

logger = setup_logging(__name__)


class Search(BaseResource):
    @required_args(["namespaces", "query"], types={"namespaces": list, "query": (str, list)})
    def query(
        self,
        namespaces: list[str],
        query: str | list[float],
        top_k: int = 10,
        threshold: float | None = None,
        kiosk_mode: bool = False,
    ) -> SearchResponse:
        """
        Performs semantic search across namespaces.

        Args:
            namespaces: A list of namespace names to search within.
            query: The search query (text string or vector list).
            top_k: The maximum number of results to return. Defaults to 10.
            threshold: Minimum similarity score (0-1). Defaults to 0.25.
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
        if not all(isinstance(ns, str) and ns for ns in namespaces):
            raise InvalidInputError("All items in 'namespaces' list must be non-empty strings.")
        if not isinstance(top_k, int) or top_k <= 0:
            raise InvalidInputError("'top_k' must be a positive integer.")
        if threshold is not None:
            if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
                raise InvalidInputError("'threshold' must be a number between 0 and 1, or None.")
            if not kiosk_mode:
                logger.warning("'threshold' is set but 'kiosk_mode' is disabled. 'threshold' will be ignored.")
        if not isinstance(kiosk_mode, bool):
            raise InvalidInputError("'kiosk_mode' must be a boolean.")
        if isinstance(query, list):
            if not query:
                raise InvalidInputError("'query' cannot be an empty list for vector search.")
            if not all(isinstance(x, (int, float)) for x in query):
                raise InvalidInputError(
                    "When 'query' is a list (vector search), all elements must be numbers."
                )

        query_type = "vector" if isinstance(query, list) else "text"
        logger.info(
            f"Attempting {query_type} search in namespace(s) '{', '.join(namespaces)}'"
            f" with top_k={top_k}, threshold={threshold}, kiosk={kiosk_mode}..."
        )

        payload: dict[str, Any] = {
            "namespaces": namespaces,
            "query": query,
            "top_k": top_k,
            "kiosk_mode": kiosk_mode,
        }
        # Only pass threshold when kiosk_mode is on; default 0.25 if not specified
        if kiosk_mode:
            payload["threshold"] = threshold if threshold is not None else 0.25

        logger.debug(f"Search payload: {payload}")

        response_data = self._client._request(
            method="POST", endpoint="/search", json_data=payload, expected_status=200
        )

        if not isinstance(response_data, dict):
            logger.error("Search response was not a dictionary.")
            raise APIError(message="Unexpected response format from search endpoint.")

        result_count = len(response_data.get("results", []))
        exec_time = response_data.get("execution_time", "N/A")
        logger.info(
            f"Search completed successfully. Found {result_count} results. Execution time: {exec_time} seconds."
        )
        return cast(SearchResponse, response_data)


class AsyncSearch(AsyncBaseResource):
    @required_args(["namespaces", "query"], types={"namespaces": list, "query": (str, list)})
    async def query(
        self,
        namespaces: list[str],
        query: str | list[float],
        top_k: int = 10,
        threshold: float | None = None,
        kiosk_mode: bool = False,
    ) -> SearchResponse:
        """
        Performs a semantic search across specified namespaces asynchronously.

        Args:
            namespaces: A list of namespace names to search within.
            query: The search query (text string or vector list).
            top_k: The number of top results to return (default: 10).
            threshold: Minimum similarity score (0-1). Defaults to 0.25.
            kiosk_mode: Whether to enable kiosk mode (default: False).

        Returns:
            A dictionary containing the search results.

            Structure:
            {
                "results": [
                    {
                        "id": str | int,
                        "score": float,
                        "text": str,
                        "metadata": dict,
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
        if not all(isinstance(ns, str) and ns for ns in namespaces):
            raise InvalidInputError("All items in 'namespaces' list must be non-empty strings.")
        if not isinstance(top_k, int) or top_k <= 0:
            raise InvalidInputError("'top_k' must be a positive integer.")
        if threshold is not None:
            if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
                raise InvalidInputError("'threshold' must be a number between 0 and 1, or None.")
            if not kiosk_mode:
                logger.warning("'threshold' is set but 'kiosk_mode' is disabled. 'threshold' will be ignored.")
        if not isinstance(kiosk_mode, bool):
            raise InvalidInputError("'kiosk_mode' must be a boolean.")
        if isinstance(query, list):
            if not query:
                raise InvalidInputError("'query' cannot be an empty list for vector search.")
            if not all(isinstance(x, (int, float)) for x in query):
                raise InvalidInputError(
                    "When 'query' is a list (vector search), all elements must be numbers."
                )

        query_type = "vector" if isinstance(query, list) else "text"
        logger.info(
            f"Attempting {query_type} search in namespace(s) '{', '.join(namespaces)}'"
            f" with top_k={top_k}, threshold={threshold}, kiosk={kiosk_mode}..."
        )

        payload: dict[str, Any] = {
            "namespaces": namespaces,
            "query": query,
            "top_k": top_k,
            "kiosk_mode": kiosk_mode,
        }
        # Only pass threshold when kiosk_mode is on; default 0.25 if not specified
        if kiosk_mode:
            payload["threshold"] = threshold if threshold is not None else 0.25

        logger.debug(f"Search payload: {payload}")

        response_data = await self._client._request(
            method="POST",
            endpoint="/search",
            json_data=payload,
            expected_status=200,
        )

        if not isinstance(response_data, dict):
            logger.error("Search response was not a dictionary.")
            raise APIError(message="Unexpected response format from search endpoint.")

        logger.info(
            f"Search completed successfully. Found {len(response_data.get('results', []))} results."
        )
        return cast(SearchResponse, response_data)
