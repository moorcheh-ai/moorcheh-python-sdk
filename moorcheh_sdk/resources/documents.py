import logging
from typing import Any

from ..exceptions import APIError, InvalidInputError
from .base import BaseResource

logger = logging.getLogger(__name__)
INVALID_ID_CHARS = [" "]


class Documents(BaseResource):
    def upload(
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
        """
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(documents, list) or not documents:
            raise InvalidInputError(
                "'documents' must be a non-empty list of dictionaries."
            )

        logger.info(
            f"Attempting to upload {len(documents)} documents to namespace"
            f" '{namespace_name}'..."
        )

        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                raise InvalidInputError(
                    f"Item at index {i} in 'documents' is not a dictionary."
                )
            if "id" not in doc or not doc["id"]:
                raise InvalidInputError(
                    f"Item at index {i} in 'documents' is missing required key 'id' or it is empty."
                )
            if isinstance(doc["id"], str) and any(
                char in doc["id"] for char in INVALID_ID_CHARS
            ):
                raise InvalidInputError(
                    f"Item at index {i} in 'documents' has an invalid ID. Invalid characters: {INVALID_ID_CHARS!r}"
                )
            if (
                "text" not in doc
                or not isinstance(doc["text"], str)
                or not doc["text"].strip()
            ):
                raise InvalidInputError(
                    f"Item at index {i} in 'documents' is missing required key 'text' or it is not a non-empty string."
                )

        endpoint = f"/namespaces/{namespace_name}/documents"
        payload = {"documents": documents}
        logger.debug(f"Upload documents payload size: {len(documents)}")

        # Expecting 202 Accepted
        response_data = self._client._request(
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

    def get(self, namespace_name: str, ids: list[str | int]) -> dict[str, Any]:
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

        response_data = self._client._request(
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

    def delete(self, namespace_name: str, ids: list[str | int]) -> dict[str, Any]:
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
        """
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError(
                "'ids' must be a non-empty list of strings or integers."
            )

        logger.info(
            f"Attempting to delete {len(ids)} document(s) from namespace"
            f" '{namespace_name}' with IDs: {ids}"
        )
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
            raise InvalidInputError(
                "All items in 'ids' list must be non-empty strings or integers."
            )

        endpoint = f"/namespaces/{namespace_name}/documents/delete"
        payload = {"ids": ids}

        # Expecting 200 OK or 207 Multi-Status
        response_data = self._client._request(
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
