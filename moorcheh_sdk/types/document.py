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


class TextDataItem(TypedDict, total=False):
    """One text or summary chunk from ``Documents.fetch_text_data``."""

    id: str
    text: str
    metadata: dict[str, Any] | None
    created_at: int
    is_summary: bool


class TextDataStatistics(TypedDict, total=False):
    total_items: int
    total_text_chunks: int
    total_summary_chunks: int
    created_at_min: int
    created_at_max: int
    source_counts: dict[str, int]


class FetchTextDataResponse(TypedDict, total=False):
    """Response from ``GET .../documents/fetch-text-data`` (keys normalized to snake_case)."""

    status: str
    message: str
    namespace: str
    statistics: TextDataStatistics
    items: list[TextDataItem]
    execution_time: float


class FileUploadResponse(TypedDict):
    success: bool
    message: str
    namespace: str
    file_name: str
    file_size: int


class FileDeleteResult(TypedDict):
    file_name: str
    status: str
    message: str


class FileDeleteResponse(TypedDict):
    success: bool
    message: str
    namespace: str
    results: list[FileDeleteResult]
