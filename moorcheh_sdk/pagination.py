from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import (
    Any,
    Generic,
    TypeVar,
)

T = TypeVar("T")


class Page(ABC, Generic[T]):
    data: list[T]

    @abstractmethod
    def __iter__(self) -> Any: ...


class AsyncPage(ABC, Generic[T]):
    data: list[T]

    @abstractmethod
    def __aiter__(self) -> Any: ...


class SyncCursorPage(Page[T]):
    data: list[T]
    next_cursor: str | None
    has_more: bool

    def __init__(
        self,
        *,
        data: list[T],
        next_cursor: str | None,
        has_more: bool,
        fetch_next: Callable[[str], "SyncCursorPage[T]"],
    ):
        self.data = data
        self.next_cursor = next_cursor
        self.has_more = has_more
        self._fetch_next = fetch_next

    def __iter__(self):
        yield from self.data

        current_page = self
        while current_page.has_more and current_page.next_cursor:
            current_page = current_page._fetch_next(current_page.next_cursor)
            yield from current_page.data


class AsyncCursorPage(AsyncPage[T]):
    data: list[T]
    next_cursor: str | None
    has_more: bool

    def __init__(
        self,
        *,
        data: list[T],
        next_cursor: str | None,
        has_more: bool,
        fetch_next: Callable[[str], Awaitable["AsyncCursorPage[T]"]],
    ):
        self.data = data
        self.next_cursor = next_cursor
        self.has_more = has_more
        self._fetch_next = fetch_next

    async def __aiter__(self):
        for item in self.data:
            yield item

        current_page = self
        while current_page.has_more and current_page.next_cursor:
            current_page = await current_page._fetch_next(current_page.next_cursor)
            for item in current_page.data:
                yield item
