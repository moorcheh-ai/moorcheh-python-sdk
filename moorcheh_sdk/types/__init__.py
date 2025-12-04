from collections.abc import Mapping
from typing import Any, TypeVar

import httpx

# Common types
JSON = dict[str, Any]
ModelT = TypeVar("ModelT")

# HTTP types
Timeout = float | httpx.Timeout | None
Headers = Mapping[str, str]
Query = Mapping[str, Any]
Body = object
