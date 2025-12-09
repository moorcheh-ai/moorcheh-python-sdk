from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._client import AsyncMoorchehClient, MoorchehClient


class BaseResource:
    """
    Base class for all Moorcheh SDK resources.

    This class provides a common initialization pattern for resources,
    ensuring they have access to the main client instance.
    """

    def __init__(self, client: "MoorchehClient") -> None:
        """
        Initialize the resource with a client instance.

        Args:
            client: The MoorchehClient instance to use for requests.
        """
        self._client = client

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(client={self._client})"


class AsyncBaseResource:
    """
    Base class for all Async Moorcheh SDK resources.
    """

    def __init__(self, client: "AsyncMoorchehClient") -> None:
        """
        Initialize the resource with a client instance.

        Args:
            client: The AsyncMoorchehClient instance to use for requests.
        """
        self._client = client

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(client={self._client})"
