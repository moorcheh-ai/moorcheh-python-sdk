# moorcheh_sdk/client.py

import httpx
import os
from typing import Optional, List, Dict, Any, Union

from .exceptions import (
    MoorchehError,
    AuthenticationError,
    InvalidInputError,
    NamespaceNotFound,
    ConflictError,
    APIError,
)

# Default base URL for the production API
DEFAULT_BASE_URL = "https://kj88v2w4p9.execute-api.us-east-2.amazonaws.com/v1" # Your confirmed endpoint

class MoorchehClient:
    """
    Python client for interacting with the Moorcheh Semantic Search API v1.
    # ... (keep __init__ and _request methods as defined previously) ...
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = 30.0,
    ):
        self.api_key = api_key or os.environ.get("MOORCHEH_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key not provided. Pass it to the constructor or set the MOORCHEH_API_KEY environment variable."
            )

        self.base_url = (base_url or os.environ.get("MOORCHEH_BASE_URL") or DEFAULT_BASE_URL).rstrip('/')
        self.timeout = timeout

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "moorcheh-python-sdk/0.1.0",
            },
            timeout=self.timeout,
        )
        print(f"MoorchehClient initialized. Base URL: {self.base_url}")

     # --- request method signature and logic ---
    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        expected_status: int = 200,
        alt_success_status: Optional[int] = None, # <-- ADDED PARAMETER HERE
    ) -> Dict[str, Any] | bytes | None:
        """Internal helper to make HTTP requests."""
        if not endpoint.startswith('/'): endpoint = '/' + endpoint
        url = f"{self.base_url}{endpoint}"
        print(f"Making {method} request to {endpoint}...")

        try:
            response = self._client.request(
                method=method,
                url=endpoint, # Relative endpoint path
                json=json_data,
                params=params,
            )

            # --- UPDATED SUCCESS CHECK ---
            is_expected_status = response.status_code == expected_status
            # Check if alt_success_status was provided and matches
            is_alt_status = alt_success_status is not None and response.status_code == alt_success_status
            # -----------------------------

            # --- UPDATED CONDITION ---
            if is_expected_status or is_alt_status:
            # -------------------------
                 # Handle No Content (e.g., successful DELETE might return 204)
                 if response.status_code == 204:
                     print(f"Request successful (Status: {response.status_code} No Content)")
                     return None
                 # Handle binary responses (like UMAP image)
                 content_type = response.headers.get("content-type", "").lower()
                 if content_type == "image/png":
                      print(f"Request successful (Status: {response.status_code}, Content-Type: PNG)")
                      return response.content
                 # Assume JSON for other successful responses
                 try:
                     print(f"Request successful (Status: {response.status_code})")
                     # Handle potentially empty JSON body on success
                     if not response.content:
                         return {}
                     return response.json()
                 except Exception as json_e:
                     print(f"Error decoding JSON response despite success status {response.status_code}: {json_e}")
                     raise APIError(status_code=response.status_code, message=f"Failed to decode JSON response: {response.text}") from json_e

            # Map HTTP error statuses to specific exceptions (remains the same)
            elif response.status_code == 400: raise InvalidInputError(message=f"Bad Request: {response.text}")
            elif response.status_code == 401 or response.status_code == 403: raise AuthenticationError(message=f"Forbidden/Unauthorized: {response.text}")
            elif response.status_code == 404:
                 if "namespace" in endpoint.lower():
                      parts = endpoint.strip('/').split('/'); ns_name = parts[1] if len(parts) > 1 and parts[0] == 'namespaces' else 'unknown'
                      raise NamespaceNotFound(namespace_name=ns_name, message=f"Resource not found: {response.text}")
                 else: raise APIError(status_code=404, message=f"Not Found: {response.text}")
            elif response.status_code == 409: raise ConflictError(message=f"Conflict: {response.text}")
            else: response.raise_for_status(); raise APIError(status_code=response.status_code, message=f"API Error: {response.text}")

        # Exception handling remains the same
        except httpx.TimeoutException as timeout_e: raise MoorchehError(f"Request timed out after {self.timeout} seconds.") from timeout_e
        except httpx.RequestError as req_e: raise MoorchehError(f"Network or request error: {req_e}") from req_e
        except Exception as e: raise MoorchehError(f"An unexpected error occurred: {e}") from e


    # --- Namespace Methods ---
    def create_namespace(
        self,
        namespace_name: str,
        type: str,
        vector_dimension: Optional[int] = None
    ) -> Dict[str, Any]:
        """Creates a new namespace."""
        # ... (Implementation from previous immersive) ...
        if not namespace_name or not isinstance(namespace_name, str): raise InvalidInputError(...)
        if type not in ['text', 'vector']: raise InvalidInputError(...)
        if type == 'vector' and (not isinstance(vector_dimension, int) or vector_dimension <= 0): raise InvalidInputError(...)
        if type == 'text' and vector_dimension is not None: raise InvalidInputError(...)
        payload = {"namespace_name": namespace_name, "type": type, "vector_dimension": vector_dimension}
        response_data = self._request("POST", "/namespaces", json_data=payload, expected_status=201)
        if not isinstance(response_data, dict): raise APIError("Unexpected response format...")
        return response_data


    def delete_namespace(self, namespace_name: str) -> None:
        """Deletes a namespace and all its associated data."""
        # ... (Implementation from previous immersive) ...
        if not namespace_name or not isinstance(namespace_name, str): raise InvalidInputError(...)
        endpoint = f"/namespaces/{namespace_name}"
        # API returns 200 with body now, not 204
        self._request("DELETE", endpoint, expected_status=200)
        print(f"Namespace '{namespace_name}' deleted successfully.")


    def list_namespaces(self) -> Dict[str, Any]:
        """
        Retrieves a list of namespaces belonging to the authenticated user,
        including metadata like type and item count.

        Returns:
            A dictionary containing the list of namespaces and execution time,
            matching the API response structure.

        Raises:
            AuthenticationError: If the API key is invalid.
            APIError: For other server errors or unexpected response format.
            MoorchehError: For network or unexpected client errors.
        """
        # Makes a GET request to the /namespaces endpoint
        # Expects a 200 OK response containing the namespace list
        response_data = self._request("GET", "/namespaces", expected_status=200)

        # Enhanced Validation: Check if the response is a dict and contains the 'namespaces' key as a list
        if not isinstance(response_data, dict):
             raise APIError(message="Unexpected response format: Expected a dictionary.")
        if 'namespaces' not in response_data or not isinstance(response_data['namespaces'], list):
             raise APIError(message="Invalid response structure: 'namespaces' key missing or not a list.")
        # Optional: Could also check for 'execution_time' key if it's guaranteed

        return response_data
    
    # --- END list_namespaces METHOD ---

    # --- upload_documents METHOD ---
    
    def upload_documents(
        self,
        namespace_name: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Uploads text documents to a text-based namespace for asynchronous
        embedding and indexing by Moorcheh.

        Args:
            namespace_name: The name of the target text-based namespace.
            documents: A list of dictionaries, where each dictionary represents
                       a document chunk. Each dictionary must contain 'id' (str/int)
                       and 'text' (str) keys. Other keys are stored as metadata.

        Returns:
            A dictionary confirming the documents were queued for processing.

        Raises:
            InvalidInputError: If input parameters are invalid or malformed.
            NamespaceNotFound: If the specified namespace doesn't exist or isn't text-based.
            AuthenticationError: If the API key is invalid.
            APIError: For other server errors.
            MoorchehError: For network or unexpected client errors.
        """
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(documents, list) or not documents:
            raise InvalidInputError("'documents' must be a non-empty list of dictionaries.")

        # Basic validation of document structure within the list
        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                raise InvalidInputError(f"Item at index {i} in 'documents' is not a dictionary.")
            if 'id' not in doc or not doc['id']: # Check for presence and non-empty
                 raise InvalidInputError(f"Item at index {i} in 'documents' is missing required key 'id' or it is empty.")
            if 'text' not in doc or not isinstance(doc['text'], str) or not doc['text'].strip():
                 raise InvalidInputError(f"Item at index {i} in 'documents' is missing required key 'text' or it is not a non-empty string.")

        endpoint = f"/namespaces/{namespace_name}/documents"
        payload = {"documents": documents}

        # Expecting 202 Accepted from the API for successful queuing
        response_data = self._request("POST", endpoint, json_data=payload, expected_status=202)

        if not isinstance(response_data, dict):
             raise APIError(message="Unexpected response format after uploading documents.")
        return response_data
    # --- END upload_documents METHOD ---

    # --- upload_vectors METHOD ---
    def upload_vectors(
        self,
        namespace_name: str,
        vectors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Uploads pre-computed vectors to a vector-based namespace.
        Moorcheh performs binarization and storage synchronously.

        Args:
            namespace_name: The name of the target vector-based namespace.
            vectors: A list of dictionaries, where each dictionary represents
                     a vector entry. Each dictionary must contain 'id' (str/int)
                     and 'vector' (List[float]) keys. An optional 'metadata'
                     dictionary can be included.

        Returns:
            A dictionary confirming the vectors were processed. The status might
            be 'success' (201) or 'partial' (207) if errors occurred.

        Raises:
            InvalidInputError: If input parameters are invalid or malformed.
            NamespaceNotFound: If the specified namespace doesn't exist or isn't vector-based.
            AuthenticationError: If the API key is invalid.
            APIError: For other server errors.
            MoorchehError: For network or unexpected client errors.
        """
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(vectors, list) or not vectors:
            raise InvalidInputError("'vectors' must be a non-empty list of dictionaries.")

        # Basic validation of vector structure within the list
        for i, vec_item in enumerate(vectors):
            if not isinstance(vec_item, dict):
                raise InvalidInputError(f"Item at index {i} in 'vectors' is not a dictionary.")
            if 'id' not in vec_item or not vec_item['id']:
                 raise InvalidInputError(f"Item at index {i} in 'vectors' is missing required key 'id' or it is empty.")
            if 'vector' not in vec_item or not isinstance(vec_item['vector'], list):
                 raise InvalidInputError(f"Item at index {i} with id '{vec_item['id']}' is missing required key 'vector' or it is not a list.")
            # Further validation (e.g., vector dimension, float type) happens server-side,
            # but basic checks can be added here if desired.

        endpoint = f"/namespaces/{namespace_name}/vectors"
        payload = {"vectors": vectors}

        # The backend Lambda might return 201 (all created) or 207 (partial success)
        # We set expected_status=201 and add alt_success_status=207
        response_data = self._request(
            method="POST",
            endpoint=endpoint,
            json_data=payload,
            expected_status=201,
            alt_success_status=207
        )

        if not isinstance(response_data, dict):
             raise APIError(message="Unexpected response format after uploading vectors.")
        return response_data
    # --- END upload_vectors METHOD ---

    # --- search METHOD ---    
    def search(
        self,
        namespaces: List[str],
        query: Union[str, List[float]],
        top_k: int = 10,
        threshold: Optional[float] = None,
        kiosk_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Performs a semantic search across one or more specified namespaces.

        Args:
            namespaces: A list of one or more namespace names to search within.
                        All namespaces must be of the same type (text or vector)
                        matching the query type.
            query: The search query, either a text string (for text namespaces)
                   or a list of floats representing a vector (for vector namespaces).
                   The vector dimension must match the target namespace(s).
            top_k: The maximum number of results to return (default: 10).
            threshold: Optional minimum ITS score (0-1) for results.
            kiosk_mode: Optional flag to apply stricter filtering (default: False).

        Returns:
            A dictionary containing the search results and execution time.

        Raises:
            InvalidInputError: If input parameters are invalid or mismatched.
            NamespaceNotFound: If any specified namespace doesn't exist.
            AuthenticationError: If the API key is invalid.
            APIError: For other server errors.
            MoorchehError: For network or unexpected client errors.
        """
        # Basic Input Validation
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

        # Prepare payload
        payload: Dict[str, Any] = {
            "namespaces": namespaces,
            "query": query,
            "top_k": top_k,
            "kiosk_mode": kiosk_mode,
        }
        # Only include threshold if it's not None
        if threshold is not None:
            payload["threshold"] = threshold

        # Make the API call - expects 200 OK
        response_data = self._request(method="POST", endpoint="/search", json_data=payload, expected_status=200)

        if not isinstance(response_data, dict):
             raise APIError(message="Unexpected response format from search endpoint.")
        # Optionally validate response structure (e.g., presence of 'results' list)
        # if 'results' not in response_data or not isinstance(response_data.get('results'), list):
        #     raise APIError(message="Search response missing 'results' list.")

        return response_data
    # --- END search METHOD ---

    # --- Data Deletion Methods ---
    def delete_documents(
        self,
        namespace_name: str,
        ids: List[Union[str, int]]
    ) -> Dict[str, Any]:
        """
        Deletes specific document chunks from a text-based namespace by their IDs.

        Args:
            namespace_name: The name of the target text-based namespace.
            ids: A list of document chunk IDs (strings or integers) to delete.

        Returns:
            A dictionary confirming the deletion status (success or partial).

        Raises:
            InvalidInputError: If input parameters are invalid.
            NamespaceNotFound: If the specified namespace doesn't exist.
            AuthenticationError: If the API key is invalid.
            APIError: For other server errors.
            MoorchehError: For network or unexpected client errors.
        """
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError("'ids' must be a non-empty list of strings or integers.")
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
             raise InvalidInputError("All items in 'ids' list must be non-empty strings or integers.")

        endpoint = f"/namespaces/{namespace_name}/documents/delete"
        payload = {"ids": ids}

        # API returns 200 OK on success, 207 Multi-Status on partial failure
        response_data = self._request(
            method="POST",
            endpoint=endpoint,
            json_data=payload,
            expected_status=200,
            alt_success_status=207
        )

        if not isinstance(response_data, dict):
             raise APIError(message="Unexpected response format after deleting documents.")
        return response_data
    # --- END delete_documents METHOD ---

    # --- delete_vectors METHOD ---
    def delete_vectors(
        self,
        namespace_name: str,
        ids: List[Union[str, int]]
    ) -> Dict[str, Any]:
        """
        Deletes specific vectors from a vector-based namespace by their IDs.

        Args:
            namespace_name: The name of the target vector-based namespace.
            ids: A list of vector IDs (strings or integers) to delete.

        Returns:
            A dictionary confirming the deletion status (success or partial).

        Raises:
            InvalidInputError: If input parameters are invalid.
            NamespaceNotFound: If the specified namespace doesn't exist.
            AuthenticationError: If the API key is invalid.
            APIError: For other server errors.
            MoorchehError: For network or unexpected client errors.
        """
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError("'ids' must be a non-empty list of strings or integers.")
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
             raise InvalidInputError("All items in 'ids' list must be non-empty strings or integers.")

        endpoint = f"/namespaces/{namespace_name}/vectors/delete"
        payload = {"ids": ids}

        # API returns 200 OK on success, 207 Multi-Status on partial failure
        response_data = self._request(
            method="POST",
            endpoint=endpoint,
            json_data=payload,
            expected_status=200,
            alt_success_status=207
        )

        if not isinstance(response_data, dict):
             raise APIError(message="Unexpected response format after deleting vectors.")
        return response_data
    # --- END delete_vectors METHOD ---


    # --- TODO: Add other methods following this pattern ---
    # get_eigenvectors(self, ...) -> Dict[str, Any]
    # get_graph(self, ...) -> Dict[str, Any]
    # get_umap_image(self, ...) -> bytes


    def close(self):
        """Closes the underlying HTTP client."""
        if hasattr(self, '_client') and self._client:
            self._client.close()
            print("MoorchehClient closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

