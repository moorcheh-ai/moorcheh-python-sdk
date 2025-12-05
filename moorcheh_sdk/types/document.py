from typing import Any, TypedDict

from .common import StatusResponse


class Document(TypedDict):
    id: str | int
    text: str
    metadata: dict[str, Any] | None


class DocumentUploadResponse(TypedDict):
    status: str
    submitted_ids: list[str | int]


class DocumentDeleteResponse(StatusResponse):
    deleted_ids: list[str | int]


class DocumentGetResponse(TypedDict):
    documents: list[Document]
