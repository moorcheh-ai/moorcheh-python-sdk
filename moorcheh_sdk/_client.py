import os
import warnings
from functools import cached_property
from typing import Any, cast

import httpx

from ._base_client import AsyncAPIClient, SyncAPIClient
from .exceptions import (
    APIError,
    AuthenticationError,
    ConflictError,
    InvalidInputError,
    MoorchehError,
    NamespaceNotFound,
)
from .resources import Answer, Documents, Namespaces, Search, Vectors
from .types import Body, Query, Timeout
from .utils.constants import DEFAULT_BASE_URL
from .utils.logging import setup_logging

logger = setup_logging(__name__)


class MoorchehClient(SyncAPIClient):
    """
    Moorcheh Python SDK client for interacting with the Moorcheh Semantic Search API v1.

    Example:
        >>> from moorcheh_sdk import MoorchehClient, MoorchehError
        >>>
        >>> try:
        ...     # Assumes MOORCHEH_API_KEY is set in environment
        ...     client = MoorchehClient()
        ...     namespaces = client.namespaces.list()
        ...     print(namespaces)
        ... except MoorchehError as e:
        ...     print(f"An error occurred: {e}")
        ... finally:
        ...     if 'client' in locals():
        ...         client.close() # Explicitly close if not using context manager

    Attributes:
        api_key (str): The API key used for authentication.
        base_url (str): The base URL of the Moorcheh API being targeted.
        timeout (float): The request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: Timeout = 30.0,
    ):
        """
        Initializes the MoorchehClient.

        Reads configuration from parameters or environment variables.
        The order of precedence for configuration is:
        1. Direct parameter (`api_key`, `base_url`).
        2. Environment variable (`MOORCHEH_API_KEY`, `MOORCHEH_BASE_URL`).
        3. Default value (for `base_url` and `timeout`).

        Args:
            api_key: Your Moorcheh API key. If None, reads from the
                `MOORCHEH_API_KEY` environment variable.
            base_url: The base URL for the Moorcheh API. If None, reads from
                the `MOORCHEH_BASE_URL` environment variable, otherwise uses
                the default production URL.
            timeout: Request timeout in seconds for HTTP requests. Defaults to 30.0.

        Raises:
            AuthenticationError: If the API key is not provided either as a
                parameter or via the `MOORCHEH_API_KEY` environment variable.
        """
        self.api_key = api_key or os.environ.get("MOORCHEH_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key not provided. Pass it to the constructor or set the"
                " MOORCHEH_API_KEY environment variable."
            )

        self.base_url = (
            base_url or os.environ.get("MOORCHEH_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

        from . import __version__ as sdk_version

        super().__init__(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            custom_headers={"User-Agent": f"moorcheh-python-sdk/{sdk_version}"},
        )

        logger.info(
            f"MoorchehClient initialized. Base URL: {self.base_url}, SDK Version:"
            f" {sdk_version}"
        )

    @cached_property
    def namespaces(self) -> Namespaces:
        return Namespaces(self)

    @cached_property
    def documents(self) -> Documents:
        return Documents(self)

    @cached_property
    def vectors(self) -> Vectors:
        return Vectors(self)

    @cached_property
    def similarity_search(self) -> Search:
        return Search(self)

    @cached_property
    def answer(self) -> Answer:
        return Answer(self)

    # --- OLD METHODS ---
    def create_namespace(
        self, namespace_name: str, type: str, vector_dimension: int | None = None
    ) -> dict[str, Any]:
        warnings.warn(
            "create_namespace is deprecated and will be removed in a future version. "
            "Use client.namespaces.create instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.namespaces.create(
            namespace_name=namespace_name, type=type, vector_dimension=vector_dimension
        )

    def delete_namespace(self, namespace_name: str) -> None:
        warnings.warn(
            "delete_namespace is deprecated and will be removed in a future version. "
            "Use client.namespaces.delete instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.namespaces.delete(namespace_name=namespace_name)

    def list_namespaces(self) -> dict[str, Any]:
        warnings.warn(
            "list_namespaces is deprecated and will be removed in a future version. "
            "Use client.namespaces.list instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.namespaces.list()

    def upload_documents(
        self, namespace_name: str, documents: list[dict[str, Any]]
    ) -> dict[str, Any]:
        warnings.warn(
            "upload_documents is deprecated and will be removed in a future version. "
            "Use client.documents.upload instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.documents.upload(namespace_name=namespace_name, documents=documents)

    def get_documents(
        self, namespace_name: str, ids: list[str | int]
    ) -> dict[str, Any]:
        warnings.warn(
            "get_documents is deprecated and will be removed in a future version. "
            "Use client.documents.get instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.documents.get(namespace_name=namespace_name, ids=ids)

    def upload_vectors(
        self, namespace_name: str, vectors: list[dict[str, Any]]
    ) -> dict[str, Any]:
        warnings.warn(
            "upload_vectors is deprecated and will be removed in a future version. "
            "Use client.vectors.upload instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.vectors.upload(namespace_name=namespace_name, vectors=vectors)

    def search(
        self,
        namespaces: list[str],
        query: str | list[float],
        top_k: int = 10,
        threshold: float | None = None,
        kiosk_mode: bool = False,
    ) -> dict[str, Any]:
        warnings.warn(
            "search is deprecated and will be removed in a future version. "
            "Use client.search.query instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.similarity_search.query(
            namespaces=namespaces,
            query=query,
            top_k=top_k,
            threshold=threshold,
            kiosk_mode=kiosk_mode,
        )

    def get_generative_answer(
        self,
        namespace: str,
        query: str,
        top_k: int = 5,
        ai_model: str = "anthropic.claude-sonnet-4-20250514-v1:0",
        chat_history: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        warnings.warn(
            "get_generative_answer is deprecated and will be removed in a future version. "
            "Use client.answer.generate instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.answer.generate(
            namespace=namespace,
            query=query,
            top_k=top_k,
            ai_model=ai_model,
            chat_history=chat_history,
            temperature=temperature,
        )

    def delete_documents(
        self, namespace_name: str, ids: list[str | int]
    ) -> dict[str, Any]:
        warnings.warn(
            "delete_documents is deprecated and will be removed in a future version. "
            "Use client.documents.delete instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.documents.delete(namespace_name=namespace_name, ids=ids)

    def delete_vectors(
        self, namespace_name: str, ids: list[str | int]
    ) -> dict[str, Any]:
        warnings.warn(
            "delete_vectors is deprecated and will be removed in a future version. "
            "Use client.vectors.delete instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.vectors.delete(namespace_name=namespace_name, ids=ids)

    # --- OLD METHODS ---

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Body | None = None,
        params: Query | None = None,
        expected_status: int = 200,
        alt_success_status: int | None = None,
    ) -> dict[str, Any] | bytes | None:
        """
        Internal helper method to make HTTP requests to the Moorcheh API.
        """
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        try:
            response = self.request(
                method=method,
                path=endpoint,
                json=json_data,
                params=params,
            )
            logger.debug(f"Received response with status code: {response.status_code}")

            return self._process_response(
                response, endpoint, expected_status, alt_success_status
            )

        except httpx.TimeoutException as timeout_e:
            logger.error(
                f"Request to {endpoint} timed out after {self.timeout} seconds.",
                exc_info=True,
            )
            raise MoorchehError(
                f"Request timed out after {self.timeout} seconds."
            ) from timeout_e
        except httpx.RequestError as req_e:
            logger.error(
                f"Network or request error for {endpoint}: {req_e}", exc_info=True
            )
            raise MoorchehError(f"Network or request error: {req_e}") from req_e
        except MoorchehError as sdk_err:
            logger.error(
                f"SDK Error during request to {endpoint}: {sdk_err}", exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during request to {endpoint}: {e}",
                exc_info=True,
            )
            raise MoorchehError(f"An unexpected error occurred: {e}") from e

    def _process_response(
        self,
        response: httpx.Response,
        endpoint: str,
        expected_status: int,
        alt_success_status: int | None,
    ) -> dict[str, Any] | bytes | None:
        is_expected_status = response.status_code == expected_status
        is_alt_status = (
            alt_success_status is not None
            and response.status_code == alt_success_status
        )

        if is_expected_status or is_alt_status:
            if response.status_code == 204:
                logger.info(
                    f"Request to {endpoint} successful (Status: 204 No Content)"
                )
                return None

            content_type = response.headers.get("content-type", "").lower()
            if content_type == "image/png":
                logger.info(
                    f"Request to {endpoint} successful (Status:"
                    f" {response.status_code}, Content-Type: PNG)"
                )
                return response.content

            try:
                logger.info(
                    f"Request to {endpoint} successful (Status: {response.status_code})"
                )
                if not response.content:
                    logger.debug("Response content is empty, returning empty dict.")
                    return {}
                json_response = response.json()
                logger.debug(f"Decoded JSON response: {json_response}")
                return cast(dict[str, Any], json_response)
            except Exception as json_e:
                # Log JSON decoding errors at WARNING level, as the status code was successful
                logger.warning(
                    "Error decoding JSON response despite success status"
                    f" {response.status_code} from {endpoint}: {json_e}",
                    exc_info=True,
                )
                raise APIError(
                    status_code=response.status_code,
                    message=f"Failed to decode JSON response: {response.text}",
                ) from json_e

        # Handle error responses
        self._handle_error_response(response, endpoint)
        return None  # Should not be reached

    def _handle_error_response(self, response: httpx.Response, endpoint: str) -> None:
        # Log error responses before raising exceptions
        logger.warning(
            f"Request to {endpoint} failed with status {response.status_code}."
            f" Response text: {response.text}"
        )

        if response.status_code == 400:
            raise InvalidInputError(message=f"Bad Request: {response.text}")
        elif response.status_code == 401 or response.status_code == 403:
            raise AuthenticationError(
                message=f"Forbidden/Unauthorized: {response.text}"
            )
        elif response.status_code == 404:
            # Try to extract namespace name for better error message if applicable
            if "namespace" in endpoint.lower() and "/namespaces/" in endpoint:
                try:
                    parts = endpoint.strip("/").split("/")
                    ns_index = parts.index("namespaces")
                    ns_name = (
                        parts[ns_index + 1] if len(parts) > ns_index + 1 else "unknown"
                    )
                except (ValueError, IndexError):
                    ns_name = "unknown"
                raise NamespaceNotFound(
                    namespace_name=ns_name,
                    message=f"Resource not found: {response.text}",
                )
            else:
                raise APIError(status_code=404, message=f"Not Found: {response.text}")
        elif response.status_code == 409:
            raise ConflictError(message=f"Conflict: {response.text}")
        else:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as http_err:
                raise APIError(
                    status_code=response.status_code,
                    message=f"API Error: {response.text}",
                ) from http_err

    def __repr__(self) -> str:
        return f"MoorchehClient(base_url='{self.base_url}', timeout={self.timeout})"


class AsyncMoorchehClient(AsyncAPIClient):
    """
    Async Moorcheh Python SDK client.

    TODO: Implement async resources and methods.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: Timeout = 30.0,
    ):
        self.api_key = api_key or os.environ.get("MOORCHEH_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key not provided. Pass it to the constructor or set the"
                " MOORCHEH_API_KEY environment variable."
            )

        self.base_url = (
            base_url or os.environ.get("MOORCHEH_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

        from . import __version__ as sdk_version

        super().__init__(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            custom_headers={"User-Agent": f"moorcheh-python-sdk/{sdk_version}"},
        )

    def __repr__(self) -> str:
        return (
            f"AsyncMoorchehClient(base_url='{self.base_url}', timeout={self.timeout})"
        )
