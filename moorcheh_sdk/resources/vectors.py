from typing import cast

from ..exceptions import APIError, InvalidInputError
from ..types import Vector, VectorDeleteResponse, VectorUploadResponse
from ..utils.batching import chunk_iterable
from ..utils.decorators import required_args
from ..utils.logging import setup_logging
from .base import AsyncBaseResource, BaseResource

logger = setup_logging(__name__)


class Vectors(BaseResource):
    @required_args(
        ["namespace_name", "vectors"], types={"namespace_name": str, "vectors": list}
    )
    def upload(
        self, namespace_name: str, vectors: list[Vector]
    ) -> VectorUploadResponse:
        """
        Uploads pre-computed vectors to a vector-based namespace.

        This process is synchronous.

        Args:
            namespace_name: The name of the target vector-based namespace.
            vectors: A list of dictionaries representing the vectors.
                Each dictionary must contain:
                - "id" (str | int): Unique identifier for the vector.
                - "vector" (list[float]): The vector embedding.
                - "metadata" (dict, optional): Additional metadata.

        Returns:
            A dictionary confirming the result of the upload.

            Structure:
            {
                "status": "success" | "partial",
                "vector_ids_processed": list[str | int],
                "errors": list[dict]
            }

        Raises:
            InvalidInputError: If input validation fails or API returns 400.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """

        logger.info(
            f"Attempting to upload {len(vectors)} vectors to namespace"
            f" '{namespace_name}'..."
        )

        for i, vec_item in enumerate(vectors):
            if not isinstance(vec_item, dict):
                raise InvalidInputError(
                    f"Item at index {i} in 'vectors' is not a dictionary."
                )
            if "id" not in vec_item or vec_item["id"] is None or vec_item["id"] == "":
                raise InvalidInputError(
                    f"Item at index {i} in 'vectors' is missing required key 'id' or it"
                    " is empty."
                )
            if "vector" not in vec_item or not isinstance(vec_item["vector"], list):
                raise InvalidInputError(
                    f"Item at index {i} with id '{vec_item['id']}' is missing required"
                    " key 'vector' or it is not a list."
                )
            if not vec_item["vector"]:
                raise InvalidInputError(
                    f"Item at index {i} with id '{vec_item['id']}' has an empty 'vector' list."
                )

        endpoint = f"/namespaces/{namespace_name}/vectors"

        all_processed_ids = []
        all_errors = []
        overall_status = "success"

        for batch in chunk_iterable(vectors, 100):
            payload = {"vectors": batch}
            logger.debug(f"Uploading batch of {len(batch)} vectors...")

            # Expecting 201 Created or 207 Multi-Status
            response_data = self._client._request(
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

            all_processed_ids.extend(response_data.get("vector_ids_processed", []))
            batch_errors = response_data.get("errors", [])
            all_errors.extend(batch_errors)

            if batch_errors or response_data.get("status") != "success":
                overall_status = "partial"

        logger.info(
            f"Upload vectors to '{namespace_name}' completed. Status:"
            f" {overall_status}, Processed: {len(all_processed_ids)}, Errors:"
            f" {len(all_errors)}"
        )
        if all_errors:
            logger.warning(f"Upload vectors encountered errors: {all_errors}")

        return {
            "status": overall_status,
            "vector_ids_processed": all_processed_ids,
            "errors": all_errors,
        }

    @required_args(
        ["namespace_name", "ids"], types={"namespace_name": str, "ids": list}
    )
    def delete(self, namespace_name: str, ids: list[str | int]) -> VectorDeleteResponse:
        """
        Deletes vectors by their IDs from a vector-based namespace.

        Args:
            namespace_name: The name of the vector-based namespace.
            ids: A list of vector IDs to delete.

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
            f"Attempting to delete {len(ids)} vector(s) from namespace"
            f" '{namespace_name}' with IDs: {ids}"
        )
        if not all(
            isinstance(item_id, (str, int)) and (item_id or item_id == 0)
            for item_id in ids
        ):
            raise InvalidInputError(
                "All items in 'ids' list must be non-empty strings or integers."
            )

        endpoint = f"/namespaces/{namespace_name}/vectors/delete"
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
        return cast(VectorDeleteResponse, response_data)


class AsyncVectors(AsyncBaseResource):
    @required_args(
        ["namespace_name", "vectors"], types={"namespace_name": str, "vectors": list}
    )
    async def upload(
        self, namespace_name: str, vectors: list[Vector]
    ) -> VectorUploadResponse:
        """
        Uploads pre-computed vectors to a vector-based namespace asynchronously.

        Args:
            namespace_name: The name of the target vector-based namespace.
            vectors: A list of dictionaries representing the vectors.
                Each dictionary must contain:
                - "id" (str | int): Unique identifier for the vector.
                - "vector" (list[float]): The vector embedding.
                - "metadata" (dict, optional): Additional metadata.

        Returns:
            A dictionary confirming the result of the upload.

            Structure:
            {
                "status": "success" | "partial",
                "vector_ids_processed": list[str | int],
                "errors": list[dict]
            }

        Raises:
            InvalidInputError: If input validation fails or API returns 400.
            NamespaceNotFound: If the namespace does not exist (404).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
            MoorchehError: For network issues.
        """
        logger.info(
            f"Attempting to upload {len(vectors)} vectors to namespace"
            f" '{namespace_name}'..."
        )

        all_processed_ids = []
        all_errors = []
        overall_status = "success"

        for batch in chunk_iterable(vectors, 100):
            response_data = await self._client._request(
                method="POST",
                endpoint=f"/namespaces/{namespace_name}/vectors",
                json_data={"vectors": batch},
                expected_status=201,
                alt_success_status=207,
            )

            if isinstance(response_data, dict):
                all_processed_ids.extend(response_data.get("vector_ids_processed", []))
                batch_errors = response_data.get("errors", [])
                all_errors.extend(batch_errors)

                if batch_errors or response_data.get("status") != "success":
                    overall_status = "partial"

        logger.info(
            f"Upload vectors to '{namespace_name}' completed. Status:"
            f" {overall_status}, Processed: {len(all_processed_ids)}, Errors:"
            f" {len(all_errors)}"
        )
        if all_errors:
            logger.warning(f"Upload vectors encountered errors: {all_errors}")

        return {
            "status": overall_status,
            "vector_ids_processed": all_processed_ids,
            "errors": all_errors,
        }

    @required_args(
        ["namespace_name", "ids"], types={"namespace_name": str, "ids": list}
    )
    async def delete(
        self, namespace_name: str, ids: list[str | int]
    ) -> VectorDeleteResponse:
        """
        Deletes vectors by their IDs from a vector-based namespace asynchronously.

        Args:
            namespace_name: The name of the vector-based namespace.
            ids: A list of vector IDs to delete.

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
            f"Attempting to delete {len(ids)} vector(s) from namespace"
            f" '{namespace_name}' with IDs: {ids}"
        )

        response_data = await self._client._request(
            method="POST",
            endpoint=f"/namespaces/{namespace_name}/vectors/delete",
            json_data={"ids": ids},
            expected_status=200,
            alt_success_status=207,
        )

        if not isinstance(response_data, dict):
            logger.error("Delete vectors response was not a dictionary.")
            raise APIError(
                message="Unexpected response format from delete vectors endpoint."
            )

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
        return cast(VectorDeleteResponse, response_data)
