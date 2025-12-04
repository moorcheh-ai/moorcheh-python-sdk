import warnings
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._client import MoorchehClient


class LegacyClientMixin:
    """
    Mixin class containing deprecated methods for MoorchehClient.
    These methods are maintained for backward compatibility but delegate
    to the new resource-based structure.
    """

    def create_namespace(
        self: "MoorchehClient",
        namespace_name: str,
        type: str,
        vector_dimension: int | None = None,
    ) -> dict[str, Any]:
        """
        [DEPRECATED] Creates a new namespace.

        Use `client.namespaces.create` instead.

        Args:
            namespace_name: A unique name for the namespace.
            type: The type of namespace ("text" or "vector").
            vector_dimension: The dimension of vectors (required if type="vector").

        Returns:
            A dictionary containing the created namespace details.

            Structure:
            {
                "message": str,
                "namespace_name": str,
                "type": str,
                "vector_dimension": int | None
            }
        """
        warnings.warn(
            "create_namespace is deprecated and will be removed in a future version. "
            "Use client.namespaces.create instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.namespaces.create(
            namespace_name=namespace_name, type=type, vector_dimension=vector_dimension
        )

    def delete_namespace(self: "MoorchehClient", namespace_name: str) -> None:
        """
        [DEPRECATED] Deletes a namespace and all its data.

        Use `client.namespaces.delete` instead.

        Args:
            namespace_name: The name of the namespace to delete.
        """
        warnings.warn(
            "delete_namespace is deprecated and will be removed in a future version. "
            "Use client.namespaces.delete instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.namespaces.delete(namespace_name=namespace_name)

    def list_namespaces(self: "MoorchehClient") -> dict[str, Any]:
        """
        [DEPRECATED] Lists all available namespaces.

        Use `client.namespaces.list` instead.

        Returns:
            A dictionary containing the list of namespaces.

            Structure:
            {
                "namespaces": [
                    {
                        "namespace_name": str,
                        "type": "text" | "vector",
                        "itemCount": int,
                        "vector_dimension": int | None
                    }
                ],
                "execution_time": float
            }
        """
        warnings.warn(
            "list_namespaces is deprecated and will be removed in a future version. "
            "Use client.namespaces.list instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.namespaces.list()

    def upload_documents(
        self: "MoorchehClient", namespace_name: str, documents: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        [DEPRECATED] Uploads text documents to a text-based namespace.

        Use `client.documents.upload` instead.

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
        """
        warnings.warn(
            "upload_documents is deprecated and will be removed in a future version. "
            "Use client.documents.upload instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.documents.upload(namespace_name=namespace_name, documents=documents)

    def get_documents(
        self: "MoorchehClient", namespace_name: str, ids: list[str | int]
    ) -> dict[str, Any]:
        """
        [DEPRECATED] Retrieves documents by their IDs from a text-based namespace.

        Use `client.documents.get` instead.

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
        """
        warnings.warn(
            "get_documents is deprecated and will be removed in a future version. "
            "Use client.documents.get instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.documents.get(namespace_name=namespace_name, ids=ids)

    def upload_vectors(
        self: "MoorchehClient", namespace_name: str, vectors: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        [DEPRECATED] Uploads pre-computed vectors to a vector-based namespace.

        Use `client.vectors.upload` instead.

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
        """
        warnings.warn(
            "upload_vectors is deprecated and will be removed in a future version. "
            "Use client.vectors.upload instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.vectors.upload(namespace_name=namespace_name, vectors=vectors)

    def search(
        self: "MoorchehClient",
        namespaces: list[str],
        query: str | list[float],
        top_k: int = 10,
        threshold: float | None = None,
        kiosk_mode: bool = False,
    ) -> dict[str, Any]:
        """
        [DEPRECATED] Performs a semantic search across namespaces.

        Use `client.similarity_search.query` instead.

        Args:
            namespaces: A list of namespace names to search within.
            query: The search query (text string or vector list).
            top_k: The maximum number of results to return. Defaults to 10.
            threshold: Minimum similarity score (0-1). Defaults to None.
            kiosk_mode: Enable strict filtering. Defaults to False.

        Returns:
            A dictionary containing search results.

            Structure:
            {
                "results": [
                    {
                        "id": str | int,
                        "score": float,
                        "text": str,  # Only for text namespaces
                        "metadata": dict
                    }
                ],
                "execution_time": float
            }
        """
        warnings.warn(
            "search is deprecated and will be removed in a future version. "
            "Use client.search.query instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.similarity_search.query(
            namespaces=namespaces,
            query=query,
            top_k=top_k,
            threshold=threshold,
            kiosk_mode=kiosk_mode,
        )

    def get_generative_answer(
        self: "MoorchehClient",
        namespace: str,
        query: str,
        top_k: int = 5,
        ai_model: str = "anthropic.claude-sonnet-4-20250514-v1:0",
        chat_history: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        [DEPRECATED] Generates an AI answer based on a search query within a namespace.

        Use `client.answer.generate` instead.

        Args:
            namespace: The name of the text-based namespace to search within.
            query: The question or prompt to answer.
            top_k: The number of search results to use as context. Defaults to 5.
            ai_model: The identifier of the LLM to use.
                Defaults to "anthropic.claude-sonnet-4-20250514-v1:0".
            chat_history: Optional list of previous conversation turns for context.
                Each item should be a dictionary. Defaults to None.
            temperature: The sampling temperature for the LLM (0.0 to 1.0).
                Higher values introduce more randomness. Defaults to 0.7.

        Returns:
            A dictionary containing the generated answer and metadata.

            Structure:
            {
                "answer": str,
                "model": str,
                "contextCount": int,
                "query": str
            }
        """
        warnings.warn(
            "get_generative_answer is deprecated and will be removed in a future version. "
            "Use client.answer.generate instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.answer.generate(
            namespace=namespace,
            query=query,
            top_k=top_k,
            ai_model=ai_model,
            chat_history=chat_history,
            temperature=temperature,
        )

    def delete_documents(
        self: "MoorchehClient", namespace_name: str, ids: list[str | int]
    ) -> dict[str, Any]:
        """
        [DEPRECATED] Deletes documents by their IDs from a text-based namespace.

        Use `client.documents.delete` instead.

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
        """
        warnings.warn(
            "delete_documents is deprecated and will be removed in a future version. "
            "Use client.documents.delete instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.documents.delete(namespace_name=namespace_name, ids=ids)

    def delete_vectors(
        self: "MoorchehClient", namespace_name: str, ids: list[str | int]
    ) -> dict[str, Any]:
        """
        [DEPRECATED] Deletes vectors by their IDs from a vector-based namespace.

        Use `client.vectors.delete` instead.

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
        """
        warnings.warn(
            "delete_vectors is deprecated and will be removed in a future version. "
            "Use client.vectors.delete instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.vectors.delete(namespace_name=namespace_name, ids=ids)
