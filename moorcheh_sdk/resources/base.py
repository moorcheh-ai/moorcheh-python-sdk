from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._client import MoorchehClient


class BaseResource:
    def __init__(self, client: "MoorchehClient"):
        self._client = client
