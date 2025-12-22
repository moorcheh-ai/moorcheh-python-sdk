from collections.abc import Mapping
from typing import Any, TypeVar

import httpx

from .answer import AnswerResponse, ChatHistoryItem
from .common import StatusResponse
from .document import (
    Document,
    DocumentDeleteResponse,
    DocumentGetResponse,
    DocumentUploadResponse,
    FileUploadResponse,
)
from .namespace import Namespace, NamespaceCreateResponse, NamespaceListResponse
from .search import SearchResponse, SearchResult
from .vector import Vector, VectorDeleteResponse, VectorUploadResponse

# Common types
JSON = dict[str, Any]
ModelT = TypeVar("ModelT")

# HTTP types
Timeout = float | httpx.Timeout | None
Headers = Mapping[str, str]
Query = Mapping[str, Any]
Body = object

__all__ = [
    "JSON",
    "ModelT",
    "Timeout",
    "Headers",
    "Query",
    "Body",
    "StatusResponse",
    "Document",
    "DocumentUploadResponse",
    "DocumentDeleteResponse",
    "DocumentGetResponse",
    "FileUploadResponse",
    "Vector",
    "VectorUploadResponse",
    "VectorDeleteResponse",
    "Namespace",
    "NamespaceCreateResponse",
    "NamespaceListResponse",
    "SearchResult",
    "SearchResponse",
    "ChatHistoryItem",
    "AnswerResponse",
]
