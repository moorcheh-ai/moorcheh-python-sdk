import os
from pathlib import Path
from typing import BinaryIO, cast

import httpx

from ..exceptions import (
    APIError,
    AuthenticationError,
    InvalidInputError,
    NamespaceNotFound,
)
from ..types import (
    Document,
    DocumentDeleteResponse,
    DocumentGetResponse,
    DocumentUploadResponse,
    FileUploadResponse,
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

    @required_args(["namespace_name"], types={"namespace_name": str})
    def upload_file(
        self,
        namespace_name: str,
        file_path: str | Path | BinaryIO,
    ) -> FileUploadResponse:
        """
        Uploads a file directly to a text-based namespace.

        The file is automatically processed to extract text content and generate
        embeddings. Files are queued for processing and uploaded via a
        pre-signed S3 URL.

        Args:
            namespace_name: The name of the target text-based namespace.
            file_path: Path to the file (str or Path) or a file-like object (BinaryIO).
                Must be one of: .pdf, .docx, .xlsx, .json, .txt, .csv, .md
                Maximum file size: 5GB

        Returns:
            A dictionary confirming the file upload.

            Structure:
            {
                "success": bool,
                "message": str,
                "namespace": str,
                "fileName": str,
                "fileSize": int
            }

        Raises:
            InvalidInputError: If file validation fails or API returns 400.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.

        Example:
            >>> client = MoorchehClient()
            >>> response = client.documents.upload_file(
            ...     namespace_name="my-docs",
            ...     file_path="document.pdf"
            ... )
            >>> print(response["message"])
            File uploaded successfully
        """
        # Allowed file extensions
        ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".json", ".txt", ".csv", ".md"}
        MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB in bytes

        # Handle file path or file-like object
        file_obj: BinaryIO
        file_name: str
        file_size: int | None

        if isinstance(file_path, (str, Path)):
            # File path provided
            path = Path(file_path)
            if not path.exists():
                raise InvalidInputError(f"File not found: {file_path}")

            file_name = path.name
            file_size = path.stat().st_size

            # Validate file extension
            file_ext = path.suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
                raise InvalidInputError(
                    f"File type '{file_ext}' is not supported. "
                    f"Allowed types: {allowed_str}"
                )

            # Validate file size
            if file_size > MAX_FILE_SIZE:
                size_gb = file_size / (1024 * 1024 * 1024)
                raise InvalidInputError(
                    f"File size ({size_gb:.2f}GB) exceeds maximum allowed size of 5GB"
                )

            file_obj = open(path, "rb")
            should_close = True
        else:
            # File-like object provided
            if not hasattr(file_path, "read"):
                raise InvalidInputError(
                    "file_path must be a file path (str/Path) or a file-like object"
                )

            file_obj = file_path  # type: ignore
            file_name = getattr(file_obj, "name", "uploaded_file")
            file_size = getattr(file_obj, "size", None)

            # Try to get file size
            if file_size is None:
                try:
                    current_pos = file_obj.tell()
                    file_obj.seek(0, os.SEEK_END)
                    file_size = file_obj.tell()
                    file_obj.seek(current_pos)
                except (AttributeError, OSError):
                    # Can't determine size, will let API validate
                    file_size = None

            # Validate file extension from filename
            file_ext = Path(file_name).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
                raise InvalidInputError(
                    f"File type '{file_ext}' is not supported. "
                    f"Allowed types: {allowed_str}"
                )

            # Validate file size if we could determine it
            if file_size is not None and file_size > MAX_FILE_SIZE:
                size_gb = file_size / (1024 * 1024 * 1024)
                raise InvalidInputError(
                    f"File size ({size_gb:.2f}GB) exceeds maximum allowed size of 5GB"
                )

            should_close = False

        logger.info(
            f"Attempting to upload file '{file_name}' ({file_size} bytes) to namespace"
            f" '{namespace_name}'..."
        )

        endpoint = f"/namespaces/{namespace_name}/upload-url"

        try:
            response_data = self._client._request(
                "POST",
                endpoint,
                json_data={"fileName": file_name},
            )

            upload_url = response_data.get("uploadUrl")
            content_type = response_data.get("contentType")
            if not upload_url or not content_type:
                raise APIError(
                    message="Upload URL response missing 'uploadUrl' or 'contentType'."
                )

            response = httpx.put(
                upload_url,
                content=file_obj,
                headers={"Content-Type": content_type},
                timeout=self._client.timeout,
            )

            logger.debug(f"Received response with status code: {response.status_code}")

            # Process response
            if response.status_code == 200:
                logger.info(
                    f"File '{file_name}' uploaded successfully to namespace"
                    f" '{namespace_name}' via presigned URL"
                )
                return cast(FileUploadResponse, {
                    "success": True,
                    "message": "File uploaded successfully",
                    "namespace": namespace_name,
                    "fileName": file_name,
                    "fileSize": file_size or 0,
                })
            else:
                # Handle error responses
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
                    # Extract namespace name for better error message
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
                else:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as http_err:
                        raise APIError(
                            status_code=response.status_code,
                            message=f"API Error: {response.text}",
                        ) from http_err
                # This line should never be reached as all error cases raise exceptions
                raise APIError(
                    status_code=response.status_code,
                    message=f"Unexpected error: {response.text}",
                )

        finally:
            if should_close and hasattr(file_obj, "close"):
                file_obj.close()


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

            response_data = await self._client._request(
                method="POST",
                endpoint=endpoint,
                json_data=payload,
                expected_status=202,
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

    @required_args(["namespace_name"], types={"namespace_name": str})
    async def upload_file(
        self,
        namespace_name: str,
        file_path: str | Path | BinaryIO,
    ) -> FileUploadResponse:
        """
        Uploads a file directly to a text-based namespace asynchronously.

        The file is automatically processed to extract text content and generate
        embeddings. Files are queued for processing.

        Args:
            namespace_name: The name of the target text-based namespace.
            file_path: Path to the file (str or Path) or a file-like object (BinaryIO).
                Must be one of: .pdf, .docx, .xlsx, .json, .txt, .csv, .md
                Maximum file size: 10MB

        Returns:
            A dictionary confirming the file upload.

            Structure:
            {
                "success": bool,
                "message": str,
                "namespace": str,
                "fileName": str,
                "fileSize": int
            }

        Raises:
            InvalidInputError: If file validation fails or API returns 400.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.

        Example:
            >>> client = AsyncMoorchehClient()
            >>> response = await client.documents.upload_file(
            ...     namespace_name="my-docs",
            ...     file_path="document.pdf"
            ... )
            >>> print(response["message"])
            File uploaded successfully
        """
        # Allowed file extensions
        ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".json", ".txt", ".csv", ".md"}
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

        # Handle file path or file-like object
        file_obj: BinaryIO
        file_name: str
        file_size: int | None

        if isinstance(file_path, (str, Path)):
            # File path provided
            path = Path(file_path)
            if not path.exists():
                raise InvalidInputError(f"File not found: {file_path}")

            file_name = path.name
            file_size = path.stat().st_size

            # Validate file extension
            file_ext = path.suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
                raise InvalidInputError(
                    f"File type '{file_ext}' is not supported. "
                    f"Allowed types: {allowed_str}"
                )

            # Validate file size
            if file_size > MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                raise InvalidInputError(
                    f"File size ({size_mb:.2f}MB) exceeds maximum allowed size of 10MB"
                )

            file_obj = open(path, "rb")
            should_close = True
        else:
            # File-like object provided
            if not hasattr(file_path, "read"):
                raise InvalidInputError(
                    "file_path must be a file path (str/Path) or a file-like object"
                )

            file_obj = file_path  # type: ignore
            file_name = getattr(file_obj, "name", "uploaded_file")
            file_size = getattr(file_obj, "size", None)

            # Try to get file size
            if file_size is None:
                try:
                    current_pos = file_obj.tell()
                    file_obj.seek(0, os.SEEK_END)
                    file_size = file_obj.tell()
                    file_obj.seek(current_pos)
                except (AttributeError, OSError):
                    # Can't determine size, will let API validate
                    file_size = 0

            # Validate file extension from filename
            file_ext = Path(file_name).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
                raise InvalidInputError(
                    f"File type '{file_ext}' is not supported. "
                    f"Allowed types: {allowed_str}"
                )

            # Validate file size if we could determine it
            if file_size > MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                raise InvalidInputError(
                    f"File size ({size_mb:.2f}MB) exceeds maximum allowed size of 10MB"
                )

            should_close = False

        logger.info(
            f"Attempting to upload file '{file_name}' ({file_size} bytes) to namespace"
            f" '{namespace_name}'..."
        )

        endpoint = f"/namespaces/{namespace_name}/upload-file"

        try:
            # Prepare multipart/form-data
            # httpx will automatically set Content-Type: multipart/form-data when files are provided
            files = {"file": (file_name, file_obj, None)}

            # Use the SDK's request method - it will handle retries and httpx will set multipart/form-data
            response = await self._client.request(
                method="POST",
                path=endpoint,
                files=files,
            )

            logger.debug(f"Received response with status code: {response.status_code}")

            # Process response
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(
                        f"File '{file_name}' uploaded successfully to namespace"
                        f" '{namespace_name}'"
                    )
                    return cast(FileUploadResponse, response_data)
                except Exception as json_e:
                    logger.error(
                        f"Error decoding JSON response: {json_e}", exc_info=True
                    )
                    raise APIError(
                        status_code=response.status_code,
                        message=f"Failed to decode JSON response: {response.text}",
                    ) from json_e
            else:
                # Handle error responses
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
                    # Extract namespace name for better error message
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
                else:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as http_err:
                        raise APIError(
                            status_code=response.status_code,
                            message=f"API Error: {response.text}",
                        ) from http_err
                # This line should never be reached as all error cases raise exceptions
                raise APIError(
                    status_code=response.status_code,
                    message=f"Unexpected error: {response.text}",
                )

        finally:
            if should_close and hasattr(file_obj, "close"):
                file_obj.close()
