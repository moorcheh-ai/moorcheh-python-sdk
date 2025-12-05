from typing import Any, TypedDict

from .common import StatusResponse


class Vector(TypedDict):
    id: str | int
    vector: list[float]
    metadata: dict[str, Any] | None


class VectorUploadResponse(StatusResponse):
    vector_ids_processed: list[str | int]


class VectorDeleteResponse(StatusResponse):
    deleted_ids: list[str | int]
