# moorcheh_sdk/client.py

import logging  # Import the logging module
import os
from typing import Any, cast

import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    ConflictError,
    InvalidInputError,
    MoorchehError,
    NamespaceNotFound,
)

# --- Setup Logger ---
# Get a logger instance for this module
logger = logging.getLogger(__name__)
# Configure default logging handler if no configuration is set by the user
# This prevents "No handler found" warnings if the user doesn't configure logging
if not logger.hasHandlers():
    logger.addHandler(logging.NullHandler())

# Default base URL for the production API
DEFAULT_BASE_URL = "https://api.moorcheh.ai/v1" # Your confirmed endpoint
INVALID_ID_CHARS = [" ",]


class MoorchehClient:
    """
    Python client for interacting with the Moorcheh Semantic Search API v1.

    Provides methods for managing namespaces, ingesting data (text or vectors),
    performing semantic searches, and deleting data.

    Example:
        >>> import os
        >>> from moorcheh_sdk import MoorchehClient, MoorchehError
        >>>
        >>> try:
        ...     # Assumes MOORCHEH_API_KEY is set in environment
        ...     client = MoorchehClient()
        ...     namespaces = client.list_namespaces()
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
            # No need to log here, the exception itself is the signal
            raise AuthenticationError(
                "API key not provided. Pass it to the constructor or set the"
                " MOORCHEH_API_KEY environment variable."
            )

        self.base_url = (
            base_url or os.environ.get("MOORCHEH_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

        # Use the SDK version from __init__.py for the User-Agent
        try:
            from . import __version__ as sdk_version
        except ImportError:
            sdk_version = "unknown"  # Fallback if import fails (shouldn't happen)

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"moorcheh-python-sdk/{sdk_version}",
            },
            timeout=self.timeout,
        )
        # Log successful initialization at INFO level
        logger.info(
            f"MoorchehClient initialized. Base URL: {self.base_url}, SDK Version:"
            f" {sdk_version}"
        )

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

    # --- Namespace Methods ---
    def create_namespace(
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

        Example:
            >>> # Create a text namespace
            >>> text_ns_info = client.create_namespace("my-documents", "text")
            >>> print(text_ns_info)
            >>>
            >>> # Create a vector namespace
            >>> vector_ns_info = client.create_namespace("my-image-vectors", "vector", 512)
            >>> print(vector_ns_info)
        """  # noqa: E501
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

        response_data = self._request(
            "POST", "/namespaces", json_data=payload, expected_status=201
        )

        if not isinstance(response_data, dict):
            # This case should ideally be caught by _request's JSON decoding, but check defensively # noqa: E501
            logger.error("Create namespace response was not a dictionary as expected.")
            raise APIError(
                message="Unexpected response format after creating namespace."
            )

        logger.info(
            f"Successfully created namespace '{namespace_name}'. Response:"
            f" {response_data}"
        )
        return response_data

    def delete_namespace(self, namespace_name: str) -> None:
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

        Example:
            >>> client.delete_namespace("my-temporary-ns")
            >>> print("Namespace deleted.") # If no exception was raised
        """
        logger.info(f"Attempting to delete namespace '{namespace_name}'...")
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")

        endpoint = f"/namespaces/{namespace_name}"
        # API returns 200 with body now, not 204
        self._request("DELETE", endpoint, expected_status=200)
        # Log success after the request confirms it (no exception raised)
        logger.info(f"Namespace '{namespace_name}' deleted successfully.")

    def list_namespaces(self) -> dict[str, Any]:
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

        Example:
            >>> ns_list_response = client.list_namespaces()
            >>> for ns in ns_list_response.get('namespaces', []):
            ...     print(f" - Name: {ns['namespace_name']}, Type: {ns['type']}")
        """
        logger.info("Attempting to list namespaces...")
        response_data = self._request("GET", "/namespaces", expected_status=200)

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

    def upload_documents(
        self, namespace_name: str, documents: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Uploads text documents to a specified text-based namespace.

        Moorcheh processes these documents asynchronously, embedding the text content
        for semantic search. Each dictionary in the `documents` list represents a
        single text chunk or document.

        Args:
            namespace_name: The name of the target *text-based* namespace.
            documents: A list of dictionaries. Each dictionary **must** contain:
                - `id` (Union[str, int]): A unique identifier for this document chunk.
                - `text` (str): The text content to be embedded and indexed.
                Any other keys in the dictionary are stored as metadata associated
                with the document chunk.

        Returns:
            A dictionary confirming the documents were successfully queued for processing.
            Example: `{'status': 'queued', 'submitted_ids': ['doc1', 'doc2']}`

        Raises:
            InvalidInputError: If `namespace_name` is invalid, `documents` is not a
                non-empty list of dictionaries, or if any dictionary within `documents`
                lacks a valid `id` or `text`. Also raised for API 400 errors.
            NamespaceNotFound: If the specified `namespace_name` does not exist or
                is not a text-based namespace (API 404 error).
            AuthenticationError: If the API key is invalid or lacks permissions.
            APIError: For other unexpected API errors during the upload request.
            MoorchehError: For network issues or client-side request problems.

        Example:
            >>> docs_to_add = [
            ...     {"id": "report-01-p1", "text": "The first paragraph...", "source": "report.pdf"},
            ...     {"id": "report-01-p2", "text": "The second paragraph...", "source": "report.pdf"},
            ... ]
            >>> upload_status = client.upload_documents("my-reports", docs_to_add)
            >>> print(upload_status)
        """  # noqa: E501
        logger.info(
            f"Attempting to upload {len(documents)} documents to namespace"
            f" '{namespace_name}'..."
        )
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(documents, list) or not documents:
            raise InvalidInputError(
                "'documents' must be a non-empty list of dictionaries."
            )

        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                raise InvalidInputError(f"Item at index {i} in 'documents' is not a dictionary.")
            if 'id' not in doc or not doc['id']:
                 raise InvalidInputError(f"Item at index {i} in 'documents' is missing required key 'id' or it is empty.")
            if any(char in doc['id'] for char in INVALID_ID_CHARS):
                 raise InvalidInputError(f"Item at index {i} in 'documents' has an invalid ID. Invalid characters: {INVALID_ID_CHARS!r}")
            if 'text' not in doc or not isinstance(doc['text'], str) or not doc['text'].strip():
                 raise InvalidInputError(f"Item at index {i} in 'documents' is missing required key 'text' or it is not a non-empty string.")

        endpoint = f"/namespaces/{namespace_name}/documents"
        payload = {"documents": documents}
        logger.debug(f"Upload documents payload size: {len(documents)}")

        # Expecting 202 Accepted
        response_data = self._request(
            "POST", endpoint, json_data=payload, expected_status=202
        )

        if not isinstance(response_data, dict):
            logger.error("Upload documents response was not a dictionary.")
            raise APIError(
                message="Unexpected response format after uploading documents."
            )

        submitted_count = len(response_data.get("submitted_ids", []))
        logger.info(
            f"Successfully queued {submitted_count} documents for upload to"
            f" '{namespace_name}'. Status: {response_data.get('status')}"
        )
        return response_data

    def get_documents(
        self, namespace_name: str, ids: list[str | int]
    ) -> dict[str, Any]:
        """
        Retrieves specific documents by their IDs from a text-based namespace.

        This endpoint allows you to fetch documents that have been previously
        uploaded and indexed, including all their metadata and content.

        Args:
            namespace_name: The name of the target text-based namespace.
            ids: A list of document IDs (strings or integers) to retrieve.
                Cannot be empty. Maximum of 100 IDs per request.

        Returns:
            A dictionary containing the retrieved documents.
            Only documents that exist in the namespace will be returned.
            Non-existent document IDs will be ignored.
            Example:
            ```json
            {
              "documents": [
                {
                  "id": "doc1",
                  "text": "Document content...",
                  "metadata": {"source": "file.txt"}
                }
              ]
            }
            ```

        Raises:
            InvalidInputError: If `namespace_name` is invalid, `ids` is not a
                non-empty list of valid IDs, or if more than 100 IDs are provided.
                Also raised for API 400 errors.
            NamespaceNotFound: If the specified `namespace_name` does not exist
                (API 404 error).
            AuthenticationError: If the API key is invalid or lacks permissions.
            APIError: For other unexpected API errors during the request.
            MoorchehError: For network issues or client-side request problems.

        Example:
            >>> doc_ids = ["doc1", "doc2"]
            >>> documents = client.get_documents("my-namespace", doc_ids)
            >>> for doc in documents.get('documents', []):
            ...     print(f"ID: {doc['id']}, Text: {doc['text'][:50]}...")
        """
        logger.info(
            f"Attempting to get {len(ids)} document(s) from namespace"
            f" '{namespace_name}'..."
        )

        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError(
                "'ids' must be a non-empty list of strings or integers."
            )
        if len(ids) > 100:
            raise InvalidInputError(
                "Maximum of 100 document IDs can be requested per call."
            )
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
            raise InvalidInputError(
                "All items in 'ids' list must be non-empty strings or integers."
            )

        endpoint = f"/namespaces/{namespace_name}/documents/get"
        payload = {"ids": ids}

        response_data = self._request(
            "POST", endpoint, json_data=payload, expected_status=200
        )

        if not isinstance(response_data, dict):
            logger.error("Get documents response was not a dictionary.")
            raise APIError(
                message="Unexpected response format from get documents endpoint."
            )

        doc_count = len(response_data.get("documents", []))
        logger.info(
            f"Successfully retrieved {doc_count} document(s) from namespace"
            f" '{namespace_name}'."
        )
        return response_data

    def upload_vectors(
        self, namespace_name: str, vectors: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Uploads pre-computed vectors to a specified vector-based namespace.

        Use this method when you have already generated vector embeddings outside
        of Moorcheh. The upload process is synchronous.

        Args:
            namespace_name: The name of the target *vector-based* namespace.
            vectors: A list of dictionaries. Each dictionary **must** contain:
                - `id` (Union[str, int]): A unique identifier for this vector.
                - `vector` (List[float]): The vector embedding as a list of floats.
                  The dimension must match the `vector_dimension` of the namespace.
                An optional `metadata` (dict) key can be included to store
                additional information associated with the vector.

        Returns:
            A dictionary confirming the result of the upload operation.
            If all vectors are processed successfully (API status 201), the 'status'
            will be 'success'. If some vectors fail (e.g., dimension mismatch)
            (API status 207), the 'status' will be 'partial', and the 'errors'
            list will contain details about the failed items.
            Example (Success): `{'status': 'success', 'vector_ids_processed': ['vec1', 'vec2'], 'errors': []}`
            Example (Partial): `{'status': 'partial', 'vector_ids_processed': ['vec1'], 'errors': [{'id': 'vec2', 'error': 'Dimension mismatch'}]}`

        Raises:
            InvalidInputError: If `namespace_name` is invalid, `vectors` is not a
                non-empty list of dictionaries, or if any dictionary within `vectors`
                lacks a valid `id` or `vector`. Also raised for API 400 errors
                (e.g., vector dimension mismatch detected server-side).
            NamespaceNotFound: If the specified `namespace_name` does not exist or
                is not a vector-based namespace (API 404 error).
            AuthenticationError: If the API key is invalid or lacks permissions.
            APIError: For other unexpected API errors during the upload request.
            MoorchehError: For network issues or client-side request problems.

        Example:
            >>> vectors_to_add = [
            ...     {"id": "img001", "vector": [0.1, 0.2, ..., 0.9], "metadata": {"label": "cat"}},
            ...     {"id": "img002", "vector": [0.5, 0.6, ..., 0.3], "metadata": {"label": "dog"}},
            ... ]
            >>> upload_status = client.upload_vectors("my-image-vectors", vectors_to_add)
            >>> print(upload_status)
        """  # noqa: E501
        logger.info(
            f"Attempting to upload {len(vectors)} vectors to namespace"
            f" '{namespace_name}'..."
        )
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(vectors, list) or not vectors:
            raise InvalidInputError(
                "'vectors' must be a non-empty list of dictionaries."
            )

        for i, vec_item in enumerate(vectors):
            if not isinstance(vec_item, dict):
                raise InvalidInputError(
                    f"Item at index {i} in 'vectors' is not a dictionary."
                )
            if "id" not in vec_item or not vec_item["id"]:
                raise InvalidInputError(
                    f"Item at index {i} in 'vectors' is missing required key 'id' or it"
                    " is empty."
                )
            if "vector" not in vec_item or not isinstance(vec_item["vector"], list):
                raise InvalidInputError(
                    f"Item at index {i} with id '{vec_item['id']}' is missing required"
                    " key 'vector' or it is not a list."
                )

        endpoint = f"/namespaces/{namespace_name}/vectors"
        payload = {"vectors": vectors}
        logger.debug(f"Upload vectors payload size: {len(vectors)}")

        # Expecting 201 Created or 207 Multi-Status
        response_data = self._request(
            method="POST",
            endpoint=endpoint,
            json_data=payload,
            expected_status=201,
            alt_success_status=207,
        )

        if not isinstance(response_data, dict):
            logger.error("Upload vectors response was not a dictionary.")
            raise APIError(
                message="Unexpected response format after uploading vectors."
            )

        processed_count = len(response_data.get("vector_ids_processed", []))
        error_count = len(response_data.get("errors", []))
        logger.info(
            f"Upload vectors to '{namespace_name}' completed. Status:"
            f" {response_data.get('status')}, Processed: {processed_count}, Errors:"
            f" {error_count}"
        )
        if error_count > 0:
            logger.warning(
                f"Upload vectors encountered errors: {response_data.get('errors')}"
            )
        return response_data

    def search(
        self,
        namespaces: list[str],
        query: str | list[float],
        top_k: int = 10,
        threshold: float | None = None,
        kiosk_mode: bool = False,
    ) -> dict[str, Any]:
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
            Example (Vector Search):
            ```json
            {
              "results": [
                {
                  "id": "vec-xyz",
                  "score": 0.92,
                  "metadata": {"label": "example"}
                }
              ],
              "execution_time": 0.088
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

        Example:
            >>> # Text search
            >>> text_results = client.search(
            ...     namespaces=["my-documents"],
            ...     query="information retrieval",
            ...     top_k=5
            ... )
            >>> print(text_results)
            >>>
            >>> # Vector search with threshold
            >>> query_vec = [0.1, 0.9, ..., 0.2]
            >>> vector_results = client.search(
            ...     namespaces=["my-image-vectors"],
            ...     query=query_vec,
            ...     top_k=3,
            ...     threshold=0.7
            ... )
            >>> print(vector_results)
        """  # noqa: E501
        query_type = "vector" if isinstance(query, list) else "text"
        logger.info(
            f"Attempting {query_type} search in namespace(s) '{', '.join(namespaces)}'"
            f" with top_k={top_k}, threshold={threshold}, kiosk={kiosk_mode}..."
        )

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

        response_data = self._request(
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

    def get_generative_answer(
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

        Example:
            >>> gen_ai_response = client.get_generative_answer(
            ...     namespace="my-faq-documents",
            ...     query="How do I reset my password?",
            ...     top_k=3
            ... )
            >>> print(gen_ai_response['answer'])
        """
        logger.info(
            "Attempting to get generative answer for query in namespace"
            f" '{namespace}'..."
        )

        # Client-side validation
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
        if chat_history is not None and not isinstance(chat_history, list):
            raise InvalidInputError(
                "'chat_history' must be a list of dictionaries or None."
            )

        # Construct the payload, converting to camelCase for the API
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

        # Assuming the endpoint is /gen-ai-answer
        response_data = self._request(
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

    def delete_documents(
        self, namespace_name: str, ids: list[str | int]
    ) -> dict[str, Any]:
        """
        Deletes specific document chunks from a text-based namespace by their IDs.

        Args:
            namespace_name: The name of the target *text-based* namespace.
            ids: A list of document chunk IDs (strings or integers) to delete.

        Returns:
            A dictionary confirming the deletion status.
            If all IDs are deleted successfully (API status 200), the 'status'
            will be 'success'. If some IDs are not found or fail (API status 207),
            the 'status' will be 'partial', and the 'errors' list will contain
            details about the failed IDs.
            Example (Success): `{'status': 'success', 'deleted_ids': ['doc1', 123], 'errors': []}`
            Example (Partial): `{'status': 'partial', 'deleted_ids': ['doc1'], 'errors': [{'id': 123, 'error': 'ID not found'}]}`

        Raises:
            InvalidInputError: If `namespace_name` is invalid or `ids` is not a
                non-empty list of valid IDs. Also raised for API 400 errors.
            NamespaceNotFound: If the specified `namespace_name` does not exist or
                is not a text-based namespace (API 404 error).
            AuthenticationError: If the API key is invalid or lacks permissions.
            APIError: For other unexpected API errors during the deletion request.
            MoorchehError: For network issues or client-side request problems.

        Example:
            >>> ids_to_remove = ["old-doc-1", "temp-doc-5"]
            >>> delete_status = client.delete_documents("my-reports", ids_to_remove)
            >>> print(delete_status)
        """  # noqa: E501
        logger.info(
            f"Attempting to delete {len(ids)} document(s) from namespace"
            f" '{namespace_name}' with IDs: {ids}"
        )
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError(
                "'ids' must be a non-empty list of strings or integers."
            )
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
            raise InvalidInputError(
                "All items in 'ids' list must be non-empty strings or integers."
            )

        endpoint = f"/namespaces/{namespace_name}/documents/delete"
        payload = {"ids": ids}

        # Expecting 200 OK or 207 Multi-Status
        response_data = self._request(
            method="POST",
            endpoint=endpoint,
            json_data=payload,
            expected_status=200,
            alt_success_status=207,
        )

        if not isinstance(response_data, dict):
            logger.error("Delete documents response was not a dictionary.")
            raise APIError(
                message="Unexpected response format after deleting documents."
            )

        deleted_count = len(response_data.get("deleted_ids", []))
        error_count = len(response_data.get("errors", []))
        logger.info(
            f"Delete documents from '{namespace_name}' completed. Status:"
            f" {response_data.get('status')}, Deleted: {deleted_count}, Errors:"
            f" {error_count}"
        )
        if error_count > 0:
            logger.warning(
                f"Delete documents encountered errors: {response_data.get('errors')}"
            )
        return response_data

    def delete_vectors(
        self, namespace_name: str, ids: list[str | int]
    ) -> dict[str, Any]:
        """
        Deletes specific vectors from a vector-based namespace by their IDs.

        Args:
            namespace_name: The name of the target *vector-based* namespace.
            ids: A list of vector IDs (strings or integers) to delete.

        Returns:
            A dictionary confirming the deletion status.
            If all IDs are deleted successfully (API status 200), the 'status'
            will be 'success'. If some IDs are not found or fail (API status 207),
            the 'status' will be 'partial', and the 'errors' list will contain
            details about the failed IDs.
            Example (Success): `{'status': 'success', 'deleted_ids': ['vec1', 456], 'errors': []}`
            Example (Partial): `{'status': 'partial', 'deleted_ids': ['vec1'], 'errors': [{'id': 456, 'error': 'ID not found'}]}`

        Raises:
            InvalidInputError: If `namespace_name` is invalid or `ids` is not a
                non-empty list of valid IDs. Also raised for API 400 errors.
            NamespaceNotFound: If the specified `namespace_name` does not exist or
                is not a vector-based namespace (API 404 error).
            AuthenticationError: If the API key is invalid or lacks permissions.
            APIError: For other unexpected API errors during the deletion request.
            MoorchehError: For network issues or client-side request problems.

        Example:
            >>> vector_ids_to_remove = ["img005", "img102"]
            >>> delete_status = client.delete_vectors("my-image-vectors", vector_ids_to_remove)
            >>> print(delete_status)
        """  # noqa: E501
        logger.info(
            f"Attempting to delete {len(ids)} vector(s) from namespace"
            f" '{namespace_name}' with IDs: {ids}"
        )
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError(
                "'ids' must be a non-empty list of strings or integers."
            )
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
            raise InvalidInputError(
                "All items in 'ids' list must be non-empty strings or integers."
            )

        endpoint = f"/namespaces/{namespace_name}/vectors/delete"
        payload = {"ids": ids}

        # Expecting 200 OK or 207 Multi-Status
        response_data = self._request(
            method="POST",
            endpoint=endpoint,
            json_data=payload,
            expected_status=200,
            alt_success_status=207,
        )

        if not isinstance(response_data, dict):
            logger.error("Delete vectors response was not a dictionary.")
            raise APIError(message="Unexpected response format after deleting vectors.")

        deleted_count = len(response_data.get("deleted_ids", []))
        error_count = len(response_data.get("errors", []))
        logger.info(
            f"Delete vectors from '{namespace_name}' completed. Status:"
            f" {response_data.get('status')}, Deleted: {deleted_count}, Errors:"
            f" {error_count}"
        )
        if error_count > 0:
            logger.warning(
                f"Delete vectors encountered errors: {response_data.get('errors')}"
            )
        return response_data

    # --- TODO: Add other methods (get_eigenvectors, get_graph, get_umap_image) ---
    # Remember to add detailed docstrings to these methods as well when implemented.

    def close(self):
        """
        Closes the underlying HTTP client connection pool.

        It's recommended to call this method when you are finished with the client
        instance, especially in long-running applications, or use the client as a
        context manager (`with MoorchehClient(...) as client:`).
        """
        if hasattr(self, "_client") and self._client:
            try:
                self._client.close()
                logger.info("MoorchehClient closed.")
            except Exception as e:
                logger.error(
                    f"Error closing underlying HTTP client: {e}", exc_info=True
                )

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context related to this object.

        Ensures the underlying HTTP client is closed.
        """
        self.close()
