import os
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
        timeout: float | None = 30.0,
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

        self.namespaces = Namespaces(self)
        self.documents = Documents(self)
        self.vectors = Vectors(self)
        self.search = Search(self)
        self.answer = Answer(self)

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        expected_status: int = 200,
        alt_success_status: int | None = None,
    ) -> dict[str, Any] | bytes | None:
        """
        Internal helper method to make HTTP requests to the Moorcheh API.

        Handles request construction, sending, response validation, error mapping,
        and basic logging. Not intended for direct use by SDK consumers.

        Args:
            method: HTTP method (e.g., "GET", "POST", "DELETE").
            endpoint: API endpoint path (e.g., "/namespaces").
            json_data: Dictionary to be sent as JSON payload in the request body.
            params: Dictionary of URL query parameters.
            expected_status: The primary expected HTTP status code for success (e.g., 200, 201).
            alt_success_status: An alternative acceptable HTTP status code for success (e.g., 207).

        Returns:
            Decoded JSON response as a dictionary, raw bytes for binary content (e.g., images),
            or None for responses with no content (e.g., 204).

        Raises:
            InvalidInputError: For 400 Bad Request errors from the API.
            AuthenticationError: For 401 Unauthorized or 403 Forbidden errors.
            NamespaceNotFound: For 404 Not Found errors specifically related to namespaces.
            ConflictError: For 409 Conflict errors from the API.
            APIError: For other 4xx/5xx HTTP errors or issues decoding a successful response.
            MoorchehError: For client-side errors like network issues or timeouts.
        """  # noqa: E501
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = f"{self.base_url}{endpoint}"  # Full URL for logging clarity
        # Log the request attempt at DEBUG level
        logger.debug(
            f"Making {method} request to {url} with payload: {json_data} and params:"
            f" {params}"
        )

        try:
            response = self._client.request(
                method=method,
                url=endpoint,  # httpx uses the relative path with base_url
                json=json_data,
                params=params,
            )
            logger.debug(f"Received response with status code: {response.status_code}")

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
                        f"Request to {endpoint} successful (Status:"
                        f" {response.status_code})"
                    )
                    if not response.content:
                        logger.debug("Response content is empty, returning empty dict.")
                        return {}
                    json_response = response.json()
                    logger.debug(f"Decoded JSON response: {json_response}")
                    return cast(dict[str, Any], json_response)
                except Exception as json_e:
                    # Log JSON decoding errors at WARNING level, as the status code was successful # noqa: E501
                    logger.warning(
                        "Error decoding JSON response despite success status"
                        f" {response.status_code} from {endpoint}: {json_e}",
                        exc_info=True,
                    )
                    raise APIError(
                        status_code=response.status_code,
                        message=f"Failed to decode JSON response: {response.text}",
                    ) from json_e

            # Log error responses before raising exceptions
            logger.warning(
                f"Request to {endpoint} failed with status {response.status_code}."
                f" Response text: {response.text}"
            )

            # Map HTTP error statuses to specific exceptions
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
                            parts[ns_index + 1]
                            if len(parts) > ns_index + 1
                            else "unknown"
                        )
                    except (ValueError, IndexError):
                        ns_name = "unknown"
                    raise NamespaceNotFound(
                        namespace_name=ns_name,
                        message=f"Resource not found: {response.text}",
                    )
                else:
                    raise APIError(
                        status_code=404, message=f"Not Found: {response.text}"
                    )
            elif response.status_code == 409:
                raise ConflictError(message=f"Conflict: {response.text}")
            else:
                # Use raise_for_status() for other 4xx/5xx errors, then wrap in APIError
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as http_err:
                    raise APIError(
                        status_code=response.status_code,
                        message=f"API Error: {response.text}",
                    ) from http_err

        # Log exceptions at ERROR level
        except httpx.TimeoutException as timeout_e:
            logger.error(
                f"Request to {url} timed out after {self.timeout} seconds.",
                exc_info=True,
            )
            raise MoorchehError(
                f"Request timed out after {self.timeout} seconds."
            ) from timeout_e
        except httpx.RequestError as req_e:
            logger.error(f"Network or request error for {url}: {req_e}", exc_info=True)
            raise MoorchehError(f"Network or request error: {req_e}") from req_e
        # Catch specific SDK exceptions if needed, but generally let them propagate
        except (
            MoorchehError
        ) as sdk_err:  # Catch our own errors if needed for specific logging
            logger.error(f"SDK Error during request to {url}: {sdk_err}", exc_info=True)
            raise  # Re-raise the original SDK error
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during request to {url}: {e}",
                exc_info=True,
            )
            raise MoorchehError(f"An unexpected error occurred: {e}") from e

        # This part should not be reachable if an error occurred and was raised
        return None  # Should only be reached in case of unhandled flow, add for safety

    # Context manager methods are inherited from SyncAPIClient


class AsyncMoorchehClient(AsyncAPIClient):
    """
    Async Moorcheh Python SDK client.

    TODO: Implement async resources and methods.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = 30.0,
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
