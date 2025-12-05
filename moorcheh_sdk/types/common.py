from typing import Any, TypedDict


class StatusResponse(TypedDict):
    status: str
    errors: list[dict[str, Any]]
