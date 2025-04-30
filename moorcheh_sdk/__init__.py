# moorcheh_sdk/__init__.py

# Expose the client and exceptions at the package level for easier imports
from .client import MoorchehClient
from .exceptions import (
    MoorchehError,
    AuthenticationError,
    InvalidInputError,
    NamespaceNotFound,
    ConflictError,
    APIError,
)

# Define package version (can be read from pyproject.toml in more advanced setups)
__version__ = "1.0.1"

# Optionally define what 'from moorcheh_sdk import *' imports
__all__ = [
    "MoorchehClient",
    "MoorchehError",
    "AuthenticationError",
    "InvalidInputError",
    "NamespaceNotFound",
    "ConflictError",
    "APIError",
    "__version__",
]
