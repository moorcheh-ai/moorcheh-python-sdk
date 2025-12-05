from typing import TypedDict


class Namespace(TypedDict):
    namespace_name: str
    type: str
    itemCount: int
    vector_dimension: int | None


class NamespaceCreateResponse(TypedDict):
    message: str
    namespace_name: str
    type: str
    vector_dimension: int | None


class NamespaceListResponse(TypedDict):
    namespaces: list[Namespace]
    execution_time: float
