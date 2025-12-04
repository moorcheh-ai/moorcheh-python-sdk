from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._client import MoorchehClient


class BaseResource:
    def __init__(self, client: "MoorchehClient"):
        self._client = client

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(client={self._client})"
