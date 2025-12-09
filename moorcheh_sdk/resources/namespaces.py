from typing import Any, cast

from ..exceptions import APIError, InvalidInputError
from ..types import NamespaceCreateResponse, NamespaceListResponse
from ..utils.decorators import required_args
from ..utils.logging import setup_logging
from .base import AsyncBaseResource, BaseResource

logger = setup_logging(__name__)


class Namespaces(BaseResource):
    @required_args(
        ["namespace_name", "type"], types={"namespace_name": str, "type": str}
    )
    def create(
        self, namespace_name: str, type: str, vector_dimension: int | None = None
    ) -> NamespaceCreateResponse:
        """
        Creates a new namespace.

        Args:
            namespace_name: A unique name for the namespace.
            type: The type of namespace ("text" or "vector").
            vector_dimension: The dimension of vectors (required if type="vector").

        Returns:
            A dictionary containing the created namespace details.

            Structure:
            {
                "message": str,
                "namespace_name": str,
                "type": str,
                "vector_dimension": int | None
            }

        Raises:
            InvalidInputError: If input validation fails or API returns 400.
            ConflictError: If the namespace already exists (409).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        logger.info(
            f"Attempting to create namespace '{namespace_name}' of type '{type}'..."
        )
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
        return cast(NamespaceCreateResponse, response_data)

    @required_args(["namespace_name"], types={"namespace_name": str})
    def delete(self, namespace_name: str) -> None:
        """
        Deletes a namespace and all its data.

        Args:
            namespace_name: The name of the namespace to delete.

        Raises:
            InvalidInputError: If input is invalid.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        logger.info(f"Attempting to delete namespace '{namespace_name}'...")

        endpoint = f"/namespaces/{namespace_name}"
        # API returns 200 with body now, not 204
        self._client._request("DELETE", endpoint, expected_status=200)
        # Log success after the request confirms it (no exception raised)
        logger.info(f"Namespace '{namespace_name}' deleted successfully.")

    def list(self) -> NamespaceListResponse:
        """
        Lists all available namespaces.

        Returns:
            A dictionary containing the list of namespaces.

            Structure:
            {
                "namespaces": [
                    {
                        "namespace_name": str,
                        "type": "text" | "vector",
                        "itemCount": int,
                        "vector_dimension": int | None
                    }
                ],
                "execution_time": float
            }

        Raises:
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
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
        return cast(NamespaceListResponse, response_data)


class AsyncNamespaces(AsyncBaseResource):
    @required_args(
        ["namespace_name", "type"], types={"namespace_name": str, "type": str}
    )
    async def create(
        self,
        namespace_name: str,
        type: str,
        vector_dimension: int | None = None,
    ) -> NamespaceCreateResponse:
        """
        Creates a new namespace asynchronously.

        Args:
            namespace_name: A unique name for the namespace.
            type: The type of namespace ("text" or "vector").
            vector_dimension: The dimension of vectors (required if type="vector").

        Returns:
            A dictionary containing the created namespace details.

        Raises:
            InvalidInputError: If input validation fails.
            ConflictError: If the namespace already exists (409).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        logger.info(
            f"Attempting to create namespace '{namespace_name}' (type={type})..."
        )

        if type not in ["text", "vector"]:
            raise InvalidInputError("Namespace type must be 'text' or 'vector'.")

        if type == "vector":
            if not isinstance(vector_dimension, int) or vector_dimension <= 0:
                raise InvalidInputError(
                    "Vector dimension must be a positive integer for type 'vector'."
                )
        elif vector_dimension is not None:
            raise InvalidInputError(
                "Vector dimension should not be provided for type 'text'."
            )

        payload = {
            "namespace_name": namespace_name,
            "type": type,
            "vector_dimension": vector_dimension,
        }

        response_data = await self._client._request(
            method="POST",
            endpoint="/namespaces",
            json_data=payload,
            expected_status=201,
        )

        logger.info(f"Namespace '{namespace_name}' created successfully.")
        return cast(NamespaceCreateResponse, response_data)

    @required_args(["namespace_name"], types={"namespace_name": str})
    async def delete(self, namespace_name: str) -> None:
        """
        Deletes a namespace and all its data asynchronously.

        Args:
            namespace_name: The name of the namespace to delete.

        Raises:
            InvalidInputError: If namespace_name is invalid.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        logger.info(f"Attempting to delete namespace '{namespace_name}'...")

        await self._client._request(
            method="DELETE",
            endpoint=f"/namespaces/{namespace_name}",
            expected_status=200,
        )

        logger.info(f"Namespace '{namespace_name}' deleted successfully.")

    async def list(self) -> NamespaceListResponse:
        """
        Lists all available namespaces asynchronously.

        Returns:
            A dictionary containing the list of namespaces.

        Raises:
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        logger.info("Attempting to list namespaces...")
        response_data = await self._client._request(
            method="GET", endpoint="/namespaces", expected_status=200
        )

        if not isinstance(response_data, dict):
            logger.error("List namespaces response was not a dictionary.")
            raise APIError(
                message="Unexpected response format from list namespaces endpoint."
            )

        if "namespaces" not in response_data or not isinstance(
            response_data["namespaces"], list
        ):
            logger.error(
                "List namespaces response missing 'namespaces' key or it is not a list."
            )
            raise APIError(
                message=(
                    "Invalid response structure: 'namespaces' key missing or not a list."
                )
            )

        logger.info(
            f"Successfully listed {len(response_data['namespaces'])} namespaces."
        )
        return cast(NamespaceListResponse, response_data)
