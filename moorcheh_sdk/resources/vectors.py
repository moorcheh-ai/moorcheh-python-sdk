from ..exceptions import APIError, InvalidInputError
from ..types import JSON
from ..utils.logging import setup_logging
from .base import BaseResource

logger = setup_logging(__name__)


class Vectors(BaseResource):
    def upload(self, namespace_name: str, vectors: list[JSON]) -> JSON:
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
        """
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(vectors, list) or not vectors:
            raise InvalidInputError(
                "'vectors' must be a non-empty list of dictionaries."
            )

        logger.info(
            f"Attempting to upload {len(vectors)} vectors to namespace"
            f" '{namespace_name}'..."
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
            if not vec_item["vector"]:
                raise InvalidInputError(
                    f"Item at index {i} with id '{vec_item['id']}' has an empty 'vector' list."
                )

        endpoint = f"/namespaces/{namespace_name}/vectors"
        payload = {"vectors": vectors}
        logger.debug(f"Upload vectors payload size: {len(vectors)}")

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

    def delete(self, namespace_name: str, ids: list[str | int]) -> JSON:
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
        """
        if not namespace_name or not isinstance(namespace_name, str):
            raise InvalidInputError("'namespace_name' must be a non-empty string.")
        if not isinstance(ids, list) or not ids:
            raise InvalidInputError(
                "'ids' must be a non-empty list of strings or integers."
            )

        logger.info(
            f"Attempting to delete {len(ids)} vector(s) from namespace"
            f" '{namespace_name}' with IDs: {ids}"
        )
        if not all(isinstance(item_id, (str, int)) and item_id for item_id in ids):
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
        return response_data
