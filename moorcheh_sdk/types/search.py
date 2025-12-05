from typing import Any, TypedDict


class SearchResult(TypedDict):
    id: str | int
    score: float
    text: str | None
    metadata: dict[str, Any]


class SearchResponse(TypedDict):
    results: list[SearchResult]
    execution_time: float
