import inspect
from collections.abc import Callable, Sequence
from functools import wraps
from typing import ParamSpec, TypeVar

from ..exceptions import InvalidInputError

P = ParamSpec("P")
R = TypeVar("R")


def required_args(
    args: Sequence[str],
    types: dict[str, type | tuple[type, ...]] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to enforce that specific arguments are provided, not None, and optionally of a specific type.

    For strings and collections, it also checks that they are not empty.

    Args:
        args: A list of argument names that are required.
        types: A dictionary mapping argument names to their expected types.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        def wrapper(*func_args: P.args, **func_kwargs: P.kwargs) -> R:
            sig = inspect.signature(func)
            try:
                bound = sig.bind(*func_args, **func_kwargs)
            except TypeError as e:
                raise InvalidInputError(str(e)) from e

            bound.apply_defaults()

            for arg_name in args:
                if arg_name not in bound.arguments:
                    continue

                val = bound.arguments[arg_name]

                if val is None:
                    raise InvalidInputError(f"Argument '{arg_name}' cannot be None.")

                if isinstance(val, (str, list, dict, set, tuple)) and not val:
                    raise InvalidInputError(f"Argument '{arg_name}' cannot be empty.")

                if types and arg_name in types:
                    expected_type = types[arg_name]
                    if not isinstance(val, expected_type):
                        raise InvalidInputError(
                            f"Argument '{arg_name}' must be of type {expected_type}."
                        )

            return func(*func_args, **func_kwargs)

        @wraps(func)
        async def async_wrapper(*func_args: P.args, **func_kwargs: P.kwargs) -> R:
            sig = inspect.signature(func)
            try:
                bound = sig.bind(*func_args, **func_kwargs)
            except TypeError as e:
                raise InvalidInputError(str(e)) from e

            bound.apply_defaults()

            for arg_name in args:
                if arg_name not in bound.arguments:
                    continue

                val = bound.arguments[arg_name]

                if val is None:
                    raise InvalidInputError(f"Argument '{arg_name}' cannot be None.")

                if isinstance(val, (str, list, dict, set, tuple)) and not val:
                    raise InvalidInputError(f"Argument '{arg_name}' cannot be empty.")

                if types and arg_name in types:
                    expected_type = types[arg_name]
                    if not isinstance(val, expected_type):
                        raise InvalidInputError(
                            f"Argument '{arg_name}' must be of type {expected_type}."
                        )

            return await func(*func_args, **func_kwargs)  # type: ignore

        if is_async:
            return async_wrapper  # type: ignore

        return wrapper

    return decorator
