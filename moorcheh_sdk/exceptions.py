from __future__ import annotations


class MoorchehError(Exception):
    def __init__(self, message="An unspecified error occurred with the Moorcheh SDK"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(MoorchehError):
    def __init__(
        self, message="Authentication failed. Check your API key and permissions."
    ):
        super().__init__(message)


class InvalidInputError(MoorchehError):
    def __init__(self, message="Invalid input provided."):
        super().__init__(message)


class NamespaceNotFound(MoorchehError):
    def __init__(self, namespace_name: str, message: str | None = None):
        self.namespace_name = namespace_name
        if message is None:
            message = f"Namespace '{namespace_name}' not found."
        super().__init__(message)


class ConflictError(MoorchehError):
    def __init__(self, message="Operation conflict."):
        super().__init__(message)


class APIError(MoorchehError):
    def __init__(
        self, status_code: int | None = None, message="An API error occurred."
    ):
        self.status_code = status_code
        full_message = (
            f"API Error (Status: {status_code}): {message}" if status_code else message
        )
        super().__init__(full_message)
