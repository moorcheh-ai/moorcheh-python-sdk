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
DEFAULT_BASE_URL = "https://kj88v2w4p9.execute-api.us-east-2.amazonaws.com/v1" # Replace if needed

class MoorchehClient:
    """
    Python client for interacting with the Moorcheh Semantic Search API v1.

    Args:
        api_key (Optional[str]): Your Moorcheh API key. If not provided,
            it will attempt to read from the MOORCHEH_API_KEY environment variable.
        base_url (Optional[str]): The base URL of the Moorcheh API. Defaults to the
            production endpoint. Useful for testing against staging or local environments.
        timeout (Optional[float]): Default request timeout in seconds. Defaults to 30.0.
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

        # Initialize httpx client
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "moorcheh-python-sdk/0.1.0", # Identify SDK
            },
            timeout=self.timeout,
            # Consider adding transport with retries for robustness
            # transport=httpx.HTTPTransport(retries=3)
        )
        print(f"MoorchehClient initialized. Base URL: {self.base_url}") # Basic init log

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        expected_status: int = 200, # Default expected success code
    ) -> Dict[str, Any] | bytes | None:
        """Internal helper to make HTTP requests."""
        url = f"{self.base_url}{endpoint}" # Ensure endpoint starts with /
        print(f"Making {method} request to {endpoint}...") # Basic request log

        try:
            response = self._client.request(
                method=method,
                url=endpoint, # httpx uses base_url + relative url
                json=json_data,
                params=params,
            )

            # Handle different success scenarios
            if response.status_code == expected_status:
                 # Handle 204 No Content specifically
                 if response.status_code == 204:
                     print(f"Request successful (Status: {response.status_code} No Content)")
                     return None # Return None for No Content

                 # Handle binary responses (like UMAP image)
                 content_type = response.headers.get("content-type", "").lower()
                 if content_type == "image/png":
                      print(f"Request successful (Status: {response.status_code}, Content-Type: PNG)")
                      return response.content # Return raw bytes

                 # Assume JSON for other successful responses
                 try:
                     print(f"Request successful (Status: {response.status_code})")
                     return response.json()
                 except Exception as json_e: # Catch JSON decode errors even on success status
                     print(f"Error decoding JSON response despite success status {response.status_code}: {json_e}")
                     raise APIError(status_code=response.status_code, message=f"Failed to decode JSON response: {response.text}")

            # Map HTTP error statuses to specific exceptions
            elif response.status_code == 400:
                raise InvalidInputError(message=f"Bad Request: {response.text}")
            elif response.status_code == 401 or response.status_code == 403:
                 raise AuthenticationError(message=f"Forbidden/Unauthorized: {response.text}")
            elif response.status_code == 404:
                 # Try to make error more specific if possible
                 if "namespace" in endpoint.lower():
                      # Extract namespace from endpoint if possible (simplistic)
                      parts = endpoint.strip('/').split('/')
                      ns_name = parts[1] if len(parts) > 1 and parts[0] == 'namespaces' else 'unknown'
                      raise NamespaceNotFound(namespace_name=ns_name, message=f"Resource not found: {response.text}")
                 else:
                      raise APIError(status_code=404, message=f"Not Found: {response.text}")
            elif response.status_code == 409:
                 raise ConflictError(message=f"Conflict: {response.text}")
            else: # General server errors or unexpected client errors
                 raise APIError(status_code=response.status_code, message=f"API Error: {response.text}")

        except httpx.TimeoutException as timeout_e:
            print(f"Request timed out: {timeout_e}")
            raise MoorchehError(f"Request timed out after {self.timeout} seconds.")
        except httpx.RequestError as req_e:
            print(f"HTTP request error: {req_e}")
            raise MoorchehError(f"Network or request error: {req_e}")
        except Exception as e:
            print(f"An unexpected error occurred during request: {e}")
            raise MoorchehError(f"An unexpected error occurred: {e}")

    # --- Namespace Methods ---
    def create_namespace(
        self,
        namespace_name: str,
        type: str,
        vector_dimension: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Creates a new namespace.

        Args:
            namespace_name: The unique name for the namespace.
            type: The type of namespace ('text' or 'vector').
            vector_dimension: The dimension of vectors if type is 'vector'. Required for vector type.

        Returns:
            A dictionary confirming the creation status.

        Raises:
            InvalidInputError: If parameters are invalid.
            ConflictError: If a namespace with that name already exists.
            AuthenticationError: If the API key is invalid.
            APIError: For other server errors.
            MoorchehError: For network or unexpected client errors.
        """
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if type not in ['text', 'vector']:
            raise InvalidInputError("'type' must be either 'text' or 'vector'.")
        if type == 'vector' and (not isinstance(vector_dimension, int) or vector_dimension <= 0):
            raise InvalidInputError("'vector_dimension' (positive integer) is required when type is 'vector'.")
        if type == 'text' and vector_dimension is not None:
             raise InvalidInputError("'vector_dimension' must not be provided when type is 'text'.")

        payload = {
            "namespace_name": namespace_name,
            "type": type,
            "vector_dimension": vector_dimension,
        }
        # Expected status for creation is 201
        response_data = self._request("POST", "/namespaces", json_data=payload, expected_status=201)
        # Ensure response is dict for type hinting, though _request should handle JSON parsing
        if not isinstance(response_data, dict):
             raise APIError(message="Unexpected response format after namespace creation.")
        return response_data

    def delete_namespace(self, namespace_name: str) -> None:
        """
        Deletes a namespace and all its associated data. This action is irreversible.

        Args:
            namespace_name: The name of the namespace to delete.

        Raises:
            NamespaceNotFound: If the namespace doesn't exist for the user.
            AuthenticationError: If the API key is invalid.
            APIError: For other server errors.
            MoorchehError: For network or unexpected client errors.
        """
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")

        endpoint = f"/namespaces/{namespace_name}"
        # Expected status for successful deletion is often 204 No Content or 200 OK with message
        # Let's try 200 first based on the lambda code returning a body
        self._request("DELETE", endpoint, expected_status=200)
        # If 204 was expected, the check inside _request handles it and returns None
        print(f"Namespace '{namespace_name}' deleted successfully.")


    # --- TODO: Add other methods following this pattern ---
    # list_namespaces(self) -> List[Dict[str, Any]]
    # upload_documents(self, namespace_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]
    # upload_vectors(self, namespace_name: str, vectors: List[Dict[str, Any]]) -> Dict[str, Any]
    # search(self, ...) -> Dict[str, Any]
    # delete_documents(self, ...) -> Dict[str, Any]
    # delete_vectors(self, ...) -> Dict[str, Any]
    # get_eigenvectors(self, ...) -> Dict[str, Any]
    # get_graph(self, ...) -> Dict[str, Any]
    # get_umap_image(self, ...) -> bytes

    def close(self):
        """Closes the underlying HTTP client."""
        if self._client:
            self._client.close()
            print("MoorchehClient closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

