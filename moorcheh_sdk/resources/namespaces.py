from typing import Any

from ..exceptions import APIError, InvalidInputError
from ..utils.logging import setup_logging
from .base import BaseResource

logger = setup_logging(__name__)


class Namespaces(BaseResource):
    def create(
        self, namespace_name: str, type: str, vector_dimension: int | None = None
    ) -> dict[str, Any]:
        """
        Creates a new namespace for storing data.

        Namespaces isolate data and configurations. Choose 'text' for storing raw text
        that Moorcheh will embed, or 'vector' for storing pre-computed vectors.

        Args:
            namespace_name: A unique name for the namespace (string). Must adhere
                to naming conventions (e.g., alphanumeric, hyphens).
            type: The type of namespace, either "text" or "vector".
            vector_dimension: The dimension of vectors that will be stored.
                Required only if `type` is "vector". Must be a positive integer.

        Returns:
            A dictionary containing the API response upon successful creation,
            typically confirming the namespace details.
            Example: `{'message': 'Namespace created successfully', 'namespace_name': 'my-text-ns', 'type': 'text'}`

        Raises:
            InvalidInputError: If `namespace_name` is invalid, `type` is not
                'text' or 'vector', `vector_dimension` is missing or invalid
                for type 'vector', or `vector_dimension` is provided for type 'text'.
                Also raised for API 400 errors.
            ConflictError: If a namespace with the given `namespace_name` already
                exists (API 409 error).
            AuthenticationError: If the API key is invalid or lacks permissions.
            APIError: For other unexpected API errors during creation.
            MoorchehError: For network issues or client-side request problems.
        """
        logger.info(
            f"Attempting to create namespace '{namespace_name}' of type '{type}'..."
        )
        # Client-side validation
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if type not in ["text", "vector"]:
            raise InvalidInputError("Namespace type must be 'text' or 'vector'.")
        if type == "vector":
            if not isinstance(vector_dimension, int) or vector_dimension <= 0:
                raise InvalidInputError(
                    "Vector dimension must be a positive integer for type 'vector'."
                )
        elif vector_dimension is not None:  # type == 'text'
            raise InvalidInputError(
                "Vector dimension should not be provided for type 'text'."
            )

        payload: dict[str, Any] = {"namespace_name": namespace_name, "type": type}
        # Only include vector_dimension if type is 'vector'
        if type == "vector":
            payload["vector_dimension"] = vector_dimension
        else:
            payload["vector_dimension"] = None  # Explicitly send None if not vector

        response_data = self._client._request(
            "POST", "/namespaces", json_data=payload, expected_status=201
        )

        if not isinstance(response_data, dict):
            logger.error("Create namespace response was not a dictionary as expected.")
            raise APIError(
                message="Unexpected response format after creating namespace."
            )

        logger.info(
            f"Successfully created namespace '{namespace_name}'. Response:"
            f" {response_data}"
        )
        return response_data

    def delete(self, namespace_name: str) -> None:
        """
        Deletes a namespace and all its associated data permanently.

        Warning: This operation is irreversible.

        Args:
            namespace_name: The exact name of the namespace to delete.

        Returns:
            None. A successful deletion is indicated by the absence of an exception.

        Raises:
            InvalidInputError: If `namespace_name` is empty or not a string.
            NamespaceNotFound: If no namespace with the given `namespace_name` exists
                (API 404 error).
            AuthenticationError: If the API key is invalid or lacks permissions.
            APIError: For other unexpected API errors during deletion.
            MoorchehError: For network issues or client-side request problems.
        """
        logger.info(f"Attempting to delete namespace '{namespace_name}'...")
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")

        endpoint = f"/namespaces/{namespace_name}"
        # API returns 200 with body now, not 204
        self._client._request("DELETE", endpoint, expected_status=200)
        # Log success after the request confirms it (no exception raised)
        logger.info(f"Namespace '{namespace_name}' deleted successfully.")

    def list(self) -> dict[str, Any]:
        """
        Retrieves a list of all namespaces accessible by the current API key.

        Returns information about each namespace, including its name, type,
        item count, and vector dimension (if applicable).

        Returns:
            A dictionary containing the API response. The list of namespaces is
            under the 'namespaces' key. Includes 'execution_time'.
            Example:
            ```json
            {
              "namespaces": [
                {
                  "namespace_name": "my-docs",
                  "type": "text",
                  "itemCount": 1250,
                  "vector_dimension": null
                },
                {
                  "namespace_name": "image-vectors",
                  "type": "vector",
                  "itemCount": 5000,
                  "vector_dimension": 512
                }
              ],
              "execution_time": 0.045
            }
            ```

        Raises:
            AuthenticationError: If the API key is invalid or lacks permissions.
            APIError: If the API returns an error or an unexpected response format
                      (e.g., missing 'namespaces' key).
            MoorchehError: For network issues or client-side request problems.
        """
        logger.info("Attempting to list namespaces...")
        response_data = self._client._request("GET", "/namespaces", expected_status=200)

        if not isinstance(response_data, dict):
            logger.error("List namespaces response was not a dictionary.")
            raise APIError(message="Unexpected response format: Expected a dictionary.")
        if "namespaces" not in response_data or not isinstance(
            response_data["namespaces"], list
        ):
            logger.error(
                "List namespaces response missing 'namespaces' key or it's not a list."
            )
            raise APIError(
                message=(
                    "Invalid response structure: 'namespaces' key missing or not a"
                    " list."
                )
            )

        count = len(response_data.get("namespaces", []))
        logger.info(f"Successfully listed {count} namespace(s).")
        logger.debug(f"List namespaces response data: {response_data}")
        return response_data
