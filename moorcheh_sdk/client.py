# moorcheh_sdk/client.py

import httpx
import os
import logging # Import the logging module
from typing import Optional, List, Dict, Any, Union

from .exceptions import (
    MoorchehError,
    AuthenticationError,
    InvalidInputError,
    NamespaceNotFound,
    ConflictError,
    APIError,
)

# --- Setup Logger ---
# Get a logger instance for this module
logger = logging.getLogger(__name__)
# Configure default logging handler if no configuration is set by the user
# This prevents "No handler found" warnings if the user doesn't configure logging
if not logger.hasHandlers():
    logger.addHandler(logging.NullHandler())

# Default base URL for the production API
DEFAULT_BASE_URL = "https://kj88v2w4p9.execute-api.us-east-2.amazonaws.com/v1" # Your confirmed endpoint

class MoorchehClient:
    """
    Python client for interacting with the Moorcheh Semantic Search API v1.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = 30.0,
    ):
        """
        Initializes the MoorchehClient.

        Args:
            api_key: Your Moorcheh API key. If None, reads from MOORCHEH_API_KEY env var.
            base_url: The base URL for the Moorcheh API. If None, reads from
                      MOORCHEH_BASE_URL env var or uses the default production URL.
            timeout: Request timeout in seconds (default: 30.0).
        
        * API key is required for authentication. get you API key from https://moorcheh.ai

        Raises:
            AuthenticationError: If the API key is not provided or found.
        """
        self.api_key = api_key or os.environ.get("MOORCHEH_API_KEY")
        if not self.api_key:
            # No need to log here, the exception itself is the signal
            raise AuthenticationError(
                "API key not provided. Pass it to the constructor or set the MOORCHEH_API_KEY environment variable."
            )

        self.base_url = (base_url or os.environ.get("MOORCHEH_BASE_URL") or DEFAULT_BASE_URL).rstrip('/')
        self.timeout = timeout

        # Use the SDK version from __init__.py for the User-Agent
        try:
            from . import __version__ as sdk_version
        except ImportError:
            sdk_version = "unknown" # Fallback if import fails (shouldn't happen)

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                f"User-Agent": f"moorcheh-python-sdk/{sdk_version}",
            },
            timeout=self.timeout,
        )
        # Log successful initialization at INFO level
        logger.info(f"MoorchehClient initialized. Base URL: {self.base_url}, SDK Version: {sdk_version}")

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        expected_status: int = 200,
        alt_success_status: Optional[int] = None,
    ) -> Dict[str, Any] | bytes | None:
        """Internal helper to make HTTP requests."""
        if not endpoint.startswith('/'): endpoint = '/' + endpoint
        url = f"{self.base_url}{endpoint}" # Full URL for logging clarity
        # Log the request attempt at DEBUG level
        logger.debug(f"Making {method} request to {url} with payload: {json_data} and params: {params}")

        try:
            response = self._client.request(
                method=method,
                url=endpoint, # httpx uses the relative path with base_url
                json=json_data,
                params=params,
            )
            logger.debug(f"Received response with status code: {response.status_code}")

            is_expected_status = response.status_code == expected_status
            is_alt_status = alt_success_status is not None and response.status_code == alt_success_status

            if is_expected_status or is_alt_status:
                 if response.status_code == 204:
                     logger.info(f"Request to {endpoint} successful (Status: 204 No Content)")
                     return None

                 content_type = response.headers.get("content-type", "").lower()
                 if content_type == "image/png":
                      logger.info(f"Request to {endpoint} successful (Status: {response.status_code}, Content-Type: PNG)")
                      return response.content

                 try:
                     logger.info(f"Request to {endpoint} successful (Status: {response.status_code})")
                     if not response.content:
                         logger.debug("Response content is empty, returning empty dict.")
                         return {}
                     json_response = response.json()
                     logger.debug(f"Decoded JSON response: {json_response}")
                     return json_response
                 except Exception as json_e:
                     # Log JSON decoding errors at WARNING level, as the status code was successful
                     logger.warning(f"Error decoding JSON response despite success status {response.status_code} from {endpoint}: {json_e}", exc_info=True)
                     raise APIError(status_code=response.status_code, message=f"Failed to decode JSON response: {response.text}") from json_e

            # Log error responses before raising exceptions
            logger.warning(f"Request to {endpoint} failed with status {response.status_code}. Response text: {response.text}")

            # Map HTTP error statuses to specific exceptions
            if response.status_code == 400: raise InvalidInputError(message=f"Bad Request: {response.text}")
            elif response.status_code == 401 or response.status_code == 403: raise AuthenticationError(message=f"Forbidden/Unauthorized: {response.text}")
            elif response.status_code == 404:
                 # Try to extract namespace name for better error message if applicable
                 if "namespace" in endpoint.lower() and "/namespaces/" in endpoint:
                      try:
                           parts = endpoint.strip('/').split('/')
                           ns_index = parts.index('namespaces')
                           ns_name = parts[ns_index + 1] if len(parts) > ns_index + 1 else 'unknown'
                      except (ValueError, IndexError):
                           ns_name = 'unknown'
                      raise NamespaceNotFound(namespace_name=ns_name, message=f"Resource not found: {response.text}")
                 else: raise APIError(status_code=404, message=f"Not Found: {response.text}")
            elif response.status_code == 409: raise ConflictError(message=f"Conflict: {response.text}")
            else:
                # Use raise_for_status() for other 4xx/5xx errors, then wrap in APIError
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as http_err:
                    raise APIError(status_code=response.status_code, message=f"API Error: {response.text}") from http_err

        # Log exceptions at ERROR level
        except httpx.TimeoutException as timeout_e:
            logger.error(f"Request to {url} timed out after {self.timeout} seconds.", exc_info=True)
            raise MoorchehError(f"Request timed out after {self.timeout} seconds.") from timeout_e
        except httpx.RequestError as req_e:
            logger.error(f"Network or request error for {url}: {req_e}", exc_info=True)
            raise MoorchehError(f"Network or request error: {req_e}") from req_e
        # Catch specific SDK exceptions if needed, but generally let them propagate
        except MoorchehError as sdk_err: # Catch our own errors if needed for specific logging
             logger.error(f"SDK Error during request to {url}: {sdk_err}", exc_info=True)
             raise # Re-raise the original SDK error
        except Exception as e:
            logger.error(f"An unexpected error occurred during request to {url}: {e}", exc_info=True)
            raise MoorchehError(f"An unexpected error occurred: {e}") from e

        # This part should not be reachable if an error occurred and was raised
        return None # Should only be reached in case of unhandled flow, add for safety


    # --- Namespace Methods ---
    def create_namespace(
        self,
        namespace_name: str,
        type: str,
        vector_dimension: Optional[int] = None
    ) -> Dict[str, Any]:
        """Creates a new namespace."""
        logger.info(f"Attempting to create namespace '{namespace_name}' of type '{type}'...")
        # Client-side validation
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if type not in ['text', 'vector']:
            raise InvalidInputError("Namespace type must be 'text' or 'vector'.")
        if type == 'vector':
            if not isinstance(vector_dimension, int) or vector_dimension <= 0:
                raise InvalidInputError("Vector dimension must be a positive integer for type 'vector'.")
        elif vector_dimension is not None: # type == 'text'
             raise InvalidInputError("Vector dimension should not be provided for type 'text'.")

        payload = {"namespace_name": namespace_name, "type": type}
        # Only include vector_dimension if type is 'vector'
        if type == 'vector':
            payload["vector_dimension"] = vector_dimension
        else:
             payload["vector_dimension"] = None # Explicitly send None if not vector

        response_data = self._request("POST", "/namespaces", json_data=payload, expected_status=201)

        if not isinstance(response_data, dict):
             # This case should ideally be caught by _request's JSON decoding, but check defensively
             logger.error("Create namespace response was not a dictionary as expected.")
             raise APIError("Unexpected response format after creating namespace.")

        logger.info(f"Successfully created namespace '{namespace_name}'. Response: {response_data}")
        return response_data


    def delete_namespace(self, namespace_name: str) -> None:
        """Deletes a namespace and all its associated data."""
        logger.info(f"Attempting to delete namespace '{namespace_name}'...")
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")

        endpoint = f"/namespaces/{namespace_name}"
        # API returns 200 with body now, not 204
        self._request("DELETE", endpoint, expected_status=200)
        # Log success after the request confirms it (no exception raised)
        logger.info(f"Namespace '{namespace_name}' deleted successfully.")


    def list_namespaces(self) -> Dict[str, Any]:
        """Retrieves a list of namespaces belonging to the authenticated user."""
        logger.info("Attempting to list namespaces...")
        response_data = self._request("GET", "/namespaces", expected_status=200)

        if not isinstance(response_data, dict):
             logger.error("List namespaces response was not a dictionary.")
             raise APIError(message="Unexpected response format: Expected a dictionary.")
        if 'namespaces' not in response_data or not isinstance(response_data['namespaces'], list):
             logger.error("List namespaces response missing 'namespaces' key or it's not a list.")
             raise APIError(message="Invalid response structure: 'namespaces' key missing or not a list.")

        count = len(response_data.get('namespaces', []))
        logger.info(f"Successfully listed {count} namespace(s).")
        logger.debug(f"List namespaces response data: {response_data}")
        return response_data

    def upload_documents(
        self,
        namespace_name: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Uploads text documents to a text-based namespace."""
        logger.info(f"Attempting to upload {len(documents)} documents to namespace '{namespace_name}'...")
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(documents, list) or not documents:
            raise InvalidInputError("'documents' must be a non-empty list of dictionaries.")

        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                raise InvalidInputError(f"Item at index {i} in 'documents' is not a dictionary.")
            if 'id' not in doc or not doc['id']:
                 raise InvalidInputError(f"Item at index {i} in 'documents' is missing required key 'id' or it is empty.")
            if 'text' not in doc or not isinstance(doc['text'], str) or not doc['text'].strip():
                 raise InvalidInputError(f"Item at index {i} in 'documents' is missing required key 'text' or it is not a non-empty string.")

        endpoint = f"/namespaces/{namespace_name}/documents"
        payload = {"documents": documents}
        logger.debug(f"Upload documents payload size: {len(documents)}")

        # Expecting 202 Accepted
        response_data = self._request("POST", endpoint, json_data=payload, expected_status=202)

        if not isinstance(response_data, dict):
             logger.error("Upload documents response was not a dictionary.")
             raise APIError(message="Unexpected response format after uploading documents.")

        submitted_count = len(response_data.get('submitted_ids', []))
        logger.info(f"Successfully queued {submitted_count} documents for upload to '{namespace_name}'. Status: {response_data.get('status')}")
        return response_data

    def upload_vectors(
        self,
        namespace_name: str,
        vectors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Uploads pre-computed vectors to a vector-based namespace."""
        logger.info(f"Attempting to upload {len(vectors)} vectors to namespace '{namespace_name}'...")
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(vectors, list) or not vectors:
            raise InvalidInputError("'vectors' must be a non-empty list of dictionaries.")

        for i, vec_item in enumerate(vectors):
            if not isinstance(vec_item, dict):
                raise InvalidInputError(f"Item at index {i} in 'vectors' is not a dictionary.")
            if 'id' not in vec_item or not vec_item['id']:
                 raise InvalidInputError(f"Item at index {i} in 'vectors' is missing required key 'id' or it is empty.")
            if 'vector' not in vec_item or not isinstance(vec_item['vector'], list):
                 raise InvalidInputError(f"Item at index {i} with id '{vec_item['id']}' is missing required key 'vector' or it is not a list.")

        endpoint = f"/namespaces/{namespace_name}/vectors"
        payload = {"vectors": vectors}
        logger.debug(f"Upload vectors payload size: {len(vectors)}")

        # Expecting 201 Created or 207 Multi-Status
        response_data = self._request(
            method="POST",
            endpoint=endpoint,
            json_data=payload,
            expected_status=201,
            alt_success_status=207
        )

        if not isinstance(response_data, dict):
             logger.error("Upload vectors response was not a dictionary.")
             raise APIError(message="Unexpected response format after uploading vectors.")

        processed_count = len(response_data.get('vector_ids_processed', []))
        error_count = len(response_data.get('errors', []))
        logger.info(f"Upload vectors to '{namespace_name}' completed. Status: {response_data.get('status')}, Processed: {processed_count}, Errors: {error_count}")
        if error_count > 0:
            logger.warning(f"Upload vectors encountered errors: {response_data.get('errors')}")
        return response_data

    def search(
        self,
        namespaces: List[str],
        query: Union[str, List[float]],
        top_k: int = 10,
        threshold: Optional[float] = None,
        kiosk_mode: bool = False
    ) -> Dict[str, Any]:
        """Performs a semantic search across one or more specified namespaces."""
        query_type = "vector" if isinstance(query, list) else "text"
        logger.info(f"Attempting {query_type} search in namespace(s) '{', '.join(namespaces)}' with top_k={top_k}, threshold={threshold}, kiosk={kiosk_mode}...")

        if not isinstance(namespaces, list) or not namespaces:
            raise InvalidInputError("'namespaces' must be a non-empty list of strings.")
        if not all(isinstance(ns, str) and ns for ns in namespaces):
            raise InvalidInputError("All items in 'namespaces' list must be non-empty strings.")
        if not query:
            raise InvalidInputError("'query' cannot be empty.")
        if not isinstance(top_k, int) or top_k <= 0:
            raise InvalidInputError("'top_k' must be a positive integer.")
        if threshold is not None and (not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1)):
             raise InvalidInputError("'threshold' must be a number between 0 and 1, or None.")
        if not isinstance(kiosk_mode, bool):
             raise InvalidInputError("'kiosk_mode' must be a boolean.")

        payload: Dict[str, Any] = {
            "namespaces": namespaces,
            "query": query, # Keep original query type
            "top_k": top_k,
            "kiosk_mode": kiosk_mode,
        }
        if threshold is not None:
            payload["threshold"] = threshold

        logger.debug(f"Search payload: {payload}") # Be careful logging query if it could be sensitive/large

        response_data = self._request(method="POST", endpoint="/search", json_data=payload, expected_status=200)

        if not isinstance(response_data, dict):
             logger.error("Search response was not a dictionary.")
             raise APIError(message="Unexpected response format from search endpoint.")

        result_count = len(response_data.get('results', []))
        exec_time = response_data.get('execution_time', 'N/A')
        logger.info(f"Search completed successfully. Found {result_count} result(s). Execution time: {exec_time}s.")
        logger.debug(f"Search results: {response_data}") # Log full results at debug level
        return response_data

    def delete_documents(
        self,
        namespace_name: str,
        ids: List[Union[str, int]]
    ) -> Dict[str, Any]:
        """Deletes specific document chunks from a text-based namespace by their IDs."""
        logger.info(f"Attempting to delete {len(ids)} document(s) from namespace '{namespace_name}' with IDs: {ids}")
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError("'ids' must be a non-empty list of strings or integers.")
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
             raise InvalidInputError("All items in 'ids' list must be non-empty strings or integers.")

        endpoint = f"/namespaces/{namespace_name}/documents/delete"
        payload = {"ids": ids}

        # Expecting 200 OK or 207 Multi-Status
        response_data = self._request(
            method="POST",
            endpoint=endpoint,
            json_data=payload,
            expected_status=200,
            alt_success_status=207
        )

        if not isinstance(response_data, dict):
             logger.error("Delete documents response was not a dictionary.")
             raise APIError(message="Unexpected response format after deleting documents.")

        deleted_count = len(response_data.get('deleted_ids', []))
        error_count = len(response_data.get('errors', []))
        logger.info(f"Delete documents from '{namespace_name}' completed. Status: {response_data.get('status')}, Deleted: {deleted_count}, Errors: {error_count}")
        if error_count > 0:
            logger.warning(f"Delete documents encountered errors: {response_data.get('errors')}")
        return response_data

    def delete_vectors(
        self,
        namespace_name: str,
        ids: List[Union[str, int]]
    ) -> Dict[str, Any]:
        """Deletes specific vectors from a vector-based namespace by their IDs."""
        logger.info(f"Attempting to delete {len(ids)} vector(s) from namespace '{namespace_name}' with IDs: {ids}")
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError("'ids' must be a non-empty list of strings or integers.")
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
             raise InvalidInputError("All items in 'ids' list must be non-empty strings or integers.")

        endpoint = f"/namespaces/{namespace_name}/vectors/delete"
        payload = {"ids": ids}

        # Expecting 200 OK or 207 Multi-Status
        response_data = self._request(
            method="POST",
            endpoint=endpoint,
            json_data=payload,
            expected_status=200,
            alt_success_status=207
        )

        if not isinstance(response_data, dict):
             logger.error("Delete vectors response was not a dictionary.")
             raise APIError(message="Unexpected response format after deleting vectors.")

        deleted_count = len(response_data.get('deleted_ids', []))
        error_count = len(response_data.get('errors', []))
        logger.info(f"Delete vectors from '{namespace_name}' completed. Status: {response_data.get('status')}, Deleted: {deleted_count}, Errors: {error_count}")
        if error_count > 0:
            logger.warning(f"Delete vectors encountered errors: {response_data.get('errors')}")
        return response_data


    # --- TODO: Add other methods (get_eigenvectors, get_graph, get_umap_image) ---
    # Remember to add logging to these methods as well when implemented.


    def close(self):
        """Closes the underlying HTTP client."""
        if hasattr(self, '_client') and self._client:
            try:
                self._client.close()
                logger.info("MoorchehClient closed.")
            except Exception as e:
                logger.error(f"Error closing underlying HTTP client: {e}", exc_info=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

