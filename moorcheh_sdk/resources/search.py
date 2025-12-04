from typing import Any

from ..exceptions import APIError, InvalidInputError
from ..types import JSON
from ..utils.logging import setup_logging
from .base import BaseResource

logger = setup_logging(__name__)


class Search(BaseResource):
    def query(
        self,
        namespaces: list[str],
        query: str | list[float],
        top_k: int = 10,
        threshold: float | None = None,
        kiosk_mode: bool = False,
    ) -> JSON:
        """
        Performs a semantic search across one or more specified namespaces.

        Searches for items (documents or vectors) that are semantically similar
        to the provided query. The query type (text or vector) must match the
        type of the target namespace(s).

        Args:
            namespaces: A list of one or more namespace names (strings) to search within.
                All listed namespaces must be of the same type ('text' or 'vector')
                and match the type of the `query`.
            query: The search query. Either:
                - A text string (str) for searching text namespaces.
                - A list of floats (List[float]) representing a vector embedding
                  for searching vector namespaces. The vector dimension must match
                  the dimension of the target vector namespace(s).
            top_k: The maximum number of results to return (default: 10). Must be
                a positive integer.
            threshold: An optional minimum similarity score (ITS score) between 0 and 1.
                Only results with a score greater than or equal to this threshold
                will be returned. Defaults to None (no threshold filtering).
            kiosk_mode: An optional boolean flag (default: False). If True, applies
                stricter filtering based on internal criteria (consult Moorcheh
                documentation for details).

        Returns:
            A dictionary containing the search results and execution time.
            The results are under the 'results' key, which is a list of dictionaries.
            Each result dictionary contains 'id', 'score', and 'metadata' (and 'text'
            for text namespace results).
            Example (Text Search):
            ```json
            {
              "results": [
                {
                  "id": "doc-abc",
                  "score": 0.85,
                  "text": "Content related to the query...",
                  "metadata": {"source": "file.txt"}
                }
              ],
              "execution_time": 0.123
            }
            ```

        Raises:
            InvalidInputError: If `namespaces` is invalid, `query` is empty,
                `top_k` is not a positive integer, `threshold` is outside the
                valid range (0-1), or `kiosk_mode` is not boolean. Also raised
                for API 400 errors (e.g., query type mismatch, vector dimension
                mismatch).
            NamespaceNotFound: If any of the specified namespaces do not exist
                (API 404 error).
            AuthenticationError: If the API key is invalid or lacks permissions.
            APIError: For other unexpected API errors during the search.
            MoorchehError: For network issues or client-side request problems.
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
        return response_data
