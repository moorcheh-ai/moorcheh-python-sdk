from collections.abc import Generator, Iterable
from typing import TypeVar

T = TypeVar("T")


def chunk_iterable(iterable: Iterable[T], size: int) -> Generator[list[T], None, None]:
    """
    Yields successive chunks from an iterable.

    Args:
        iterable: The iterable to chunk.
        size: The size of each chunk.

    Yields:
        A list containing 'size' elements from the iterable.
    """
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
