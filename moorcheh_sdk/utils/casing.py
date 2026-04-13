import re
from typing import Any

_FIRST_CAP_RE = re.compile(r"(.)([A-Z][a-z]+)")
_ALL_CAP_RE = re.compile(r"([a-z0-9])([A-Z])")


def to_snake_case(value: str) -> str:
    """
    Convert camelCase/PascalCase strings to snake_case.
    """
    s1 = _FIRST_CAP_RE.sub(r"\1_\2", value)
    return _ALL_CAP_RE.sub(r"\1_\2", s1).lower()


def transform_keys_to_snake_case(value: Any) -> Any:
    """
    Recursively convert dictionary keys to snake_case.
    """
    if isinstance(value, dict):
        return {
            to_snake_case(str(key)): transform_keys_to_snake_case(val)
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [transform_keys_to_snake_case(item) for item in value]
    return value
