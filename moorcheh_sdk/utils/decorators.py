import inspect
from collections.abc import Callable, Sequence
from functools import wraps
from typing import Any

from ..exceptions import InvalidInputError


def required_args(
    args: Sequence[str],
    types: dict[str, type | tuple[type, ...]] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to enforce that specific arguments are provided, not None, and optionally of a specific type.

    For strings and collections, it also checks that they are not empty.

    Args:
        args: A list of argument names that are required.
        types: A dictionary mapping argument names to their expected types.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*func_args: Any, **func_kwargs: Any) -> Any:
            sig = inspect.signature(func)
            try:
                bound = sig.bind(*func_args, **func_kwargs)
            except TypeError as e:
                raise InvalidInputError(str(e)) from e

            bound.apply_defaults()

            for arg_name in args:
                if arg_name not in bound.arguments:
                    # This might happen if the argument is not in the signature,
                    # but if it is in 'args' list it should be expected.
                    # However, bind() would fail if a required arg is missing unless it has a default.
                    # If it has a default of None, we might want to catch it here.
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

        return wrapper

    return decorator
