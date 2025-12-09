from typing import cast

from ..exceptions import APIError, InvalidInputError
from ..types import (
    Document,
    DocumentDeleteResponse,
    DocumentGetResponse,
    DocumentUploadResponse,
)
from ..utils.batching import chunk_iterable
from ..utils.constants import INVALID_ID_CHARS
from ..utils.decorators import required_args
from ..utils.logging import setup_logging
from .base import AsyncBaseResource, BaseResource

logger = setup_logging(__name__)


class Documents(BaseResource):
    @required_args(
        ["namespace_name", "documents"],
        types={"namespace_name": str, "documents": list},
    )
    def upload(
        self, namespace_name: str, documents: list[Document]
    ) -> DocumentUploadResponse:
        """
        Uploads text documents to a text-based namespace.

        This process is asynchronous. Documents are queued for embedding and indexing.

        Args:
            namespace_name: The name of the target text-based namespace.
            documents: A list of dictionaries representing the documents.
                Each dictionary must contain:
                - "id" (str | int): Unique identifier for the document.
                - "text" (str): The text content to embed.
                - "metadata" (dict, optional): Additional metadata.

        Returns:
            A dictionary confirming the documents were queued.

            Structure:
            {
                "status": "queued",
                "submitted_ids": list[str | int]
            }

        Raises:
            InvalidInputError: If input validation fails or API returns 400.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """

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

        all_submitted_ids = []

        for batch in chunk_iterable(documents, 100):
            payload = {"documents": batch}
            logger.debug(f"Uploading batch of {len(batch)} documents...")

            # Expecting 202 Accepted
            response_data = self._client._request(
                "POST", endpoint, json_data=payload, expected_status=202
            )

            if not isinstance(response_data, dict):
                logger.error("Upload documents response was not a dictionary.")
                raise APIError(
                    message="Unexpected response format after uploading documents."
                )

            all_submitted_ids.extend(response_data.get("submitted_ids", []))

        logger.info(
            f"Successfully queued {len(all_submitted_ids)} documents for upload to"
            f" '{namespace_name}'."
        )

        return {"status": "queued", "submitted_ids": all_submitted_ids}

    @required_args(
        ["namespace_name", "ids"], types={"namespace_name": str, "ids": list}
    )
    def get(self, namespace_name: str, ids: list[str | int]) -> DocumentGetResponse:
        """
        Retrieves documents by their IDs from a text-based namespace.

        Args:
            namespace_name: The name of the text-based namespace.
            ids: A list of document IDs to retrieve (max 100).

        Returns:
            A dictionary containing the retrieved documents.

            Structure:
            {
                "documents": [
                    {
                        "id": str | int,
                        "text": str,
                        "metadata": dict
                    }
                ]
            }

        Raises:
            InvalidInputError: If input is invalid or >100 IDs requested.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        if len(ids) > 100:
            raise InvalidInputError(
                "Maximum of 100 document IDs can be requested per call."
            )
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
            raise InvalidInputError(
                "All items in 'ids' list must be non-empty strings or integers."
            )

        logger.info(
            f"Attempting to get {len(ids)} document(s) from namespace"
            f" '{namespace_name}'..."
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
        return cast(DocumentGetResponse, response_data)

    @required_args(
        ["namespace_name", "ids"], types={"namespace_name": str, "ids": list}
    )
    def delete(
        self, namespace_name: str, ids: list[str | int]
    ) -> DocumentDeleteResponse:
        """
        Deletes documents by their IDs from a text-based namespace.

        Args:
            namespace_name: The name of the text-based namespace.
            ids: A list of document IDs to delete.

        Returns:
            A dictionary confirming the deletion status.

            Structure:
            {
                "status": "success" | "partial",
                "deleted_ids": list[str | int],
                "errors": list[dict]
            }

        Raises:
            InvalidInputError: If input is invalid.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        logger.info(
            f"Attempting to delete {len(ids)} document(s) from namespace"
            f" '{namespace_name}' with IDs: {ids}"
        )
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
            raise InvalidInputError(
                "All items in 'ids' list must be non-empty strings or integers."
            )

        response_data = self._client._request(
            method="POST",
            endpoint=f"/namespaces/{namespace_name}/documents/delete",
            json_data={"ids": ids},
            expected_status=200,
            alt_success_status=207,
        )

        if not isinstance(response_data, dict):
            logger.error("Delete documents response was not a dictionary.")
            raise APIError(
                message="Unexpected response format from delete documents endpoint."
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
        return cast(DocumentDeleteResponse, response_data)


class AsyncDocuments(AsyncBaseResource):
    @required_args(
        ["namespace_name", "documents"],
        types={"namespace_name": str, "documents": list},
    )
    async def upload(
        self, namespace_name: str, documents: list[Document]
    ) -> DocumentUploadResponse:
        """
        Uploads text documents to a text-based namespace asynchronously.

        This process is asynchronous (fire-and-forget style on the server),
        so the response confirms queuing, not completion.

        Args:
            namespace_name: The name of the target text-based namespace.
            documents: A list of dictionaries representing the documents.
                Each dictionary must contain:
                - "id" (str | int): Unique identifier for the document.
                - "text" (str): The text content to embed.
                - "metadata" (dict, optional): Additional metadata.

        Returns:
            A dictionary confirming the documents were queued.

            Structure:
            {
                "status": "queued",
                "submitted_ids": list[str | int]
            }

        Raises:
            InvalidInputError: If input validation fails or API returns 400.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        logger.info(
            f"Attempting to upload {len(documents)} documents to namespace"
            f" '{namespace_name}'..."
        )

        all_submitted_ids = []

        for batch in chunk_iterable(documents, 100):
            response_data = await self._client._request(
                method="POST",
                endpoint=f"/namespaces/{namespace_name}/documents",
                json_data={"documents": batch},
                expected_status=202,
            )

            if isinstance(response_data, dict):
                all_submitted_ids.extend(response_data.get("submitted_ids", []))

        logger.info(
            f"Successfully queued {len(all_submitted_ids)} documents for upload to"
            f" '{namespace_name}'."
        )
        return {"status": "queued", "submitted_ids": all_submitted_ids}

    @required_args(
        ["namespace_name", "ids"], types={"namespace_name": str, "ids": list}
    )
    async def get(
        self, namespace_name: str, ids: list[str | int]
    ) -> DocumentGetResponse:
        """
        Retrieves documents by their IDs from a text-based namespace asynchronously.

        Args:
            namespace_name: The name of the text-based namespace.
            ids: A list of document IDs to retrieve (max 100).

        Returns:
            A dictionary containing the retrieved documents.

            Structure:
            {
                "documents": [
                    {
                        "id": str | int,
                        "text": str,
                        "metadata": dict
                    }
                ]
            }

        Raises:
            InvalidInputError: If input is invalid.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        if len(ids) > 100:
            raise InvalidInputError(
                "Maximum of 100 document IDs can be requested per call."
            )

        # Check for invalid characters in IDs (client-side validation)
        # Assuming IDs should be alphanumeric, dashes, or underscores.
        # Adjust regex as per API requirements.
        import re

        invalid_id_pattern = re.compile(r"[^a-zA-Z0-9_\-]")
        for doc_id in ids:
            if isinstance(doc_id, str) and invalid_id_pattern.search(doc_id):
                raise InvalidInputError(
                    f"Invalid characters in document ID: '{doc_id}'. IDs should be"
                    " alphanumeric."
                )

        logger.info(
            f"Attempting to retrieve {len(ids)} document(s) from namespace"
            f" '{namespace_name}'..."
        )

        response_data = await self._client._request(
            method="POST",
            endpoint=f"/namespaces/{namespace_name}/documents/get",
            json_data={"ids": ids},
            expected_status=200,
        )

        if not isinstance(response_data, dict):
            logger.error("Get documents response was not a dictionary.")
            raise APIError(
                message="Unexpected response format from get documents endpoint."
            )

        retrieved_count = len(response_data.get("documents", []))
        logger.info(f"Successfully retrieved {retrieved_count} document(s).")
        return cast(DocumentGetResponse, response_data)

    @required_args(
        ["namespace_name", "ids"], types={"namespace_name": str, "ids": list}
    )
    async def delete(
        self, namespace_name: str, ids: list[str | int]
    ) -> DocumentDeleteResponse:
        """
        Deletes documents by their IDs from a text-based namespace asynchronously.

        Args:
            namespace_name: The name of the text-based namespace.
            ids: A list of document IDs to delete.

        Returns:
            A dictionary confirming the deletion status.

            Structure:
            {
                "status": "success" | "partial",
                "deleted_ids": list[str | int],
                "errors": list[dict]
            }

        Raises:
            InvalidInputError: If input is invalid.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        logger.info(
            f"Attempting to delete {len(ids)} document(s) from namespace"
            f" '{namespace_name}' with IDs: {ids}"
        )

        response_data = await self._client._request(
            method="POST",
            endpoint=f"/namespaces/{namespace_name}/documents/delete",
            json_data={"ids": ids},
            expected_status=200,
            alt_success_status=207,
        )

        if not isinstance(response_data, dict):
            logger.error("Delete documents response was not a dictionary.")
            raise APIError(
                message="Unexpected response format from delete documents endpoint."
            )

        logger.info(
            f"Delete operation completed with status: {response_data.get('status')}"
        )
        return cast(DocumentDeleteResponse, response_data)
