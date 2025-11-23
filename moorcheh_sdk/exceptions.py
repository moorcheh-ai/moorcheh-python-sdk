# moorcheh_sdk/exceptions.py


class MoorchehError(Exception):
    """Base exception class for all Moorcheh SDK errors."""

    def __init__(self, message="An unspecified error occurred with the Moorcheh SDK"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(MoorchehError):
    """Raised when API key is invalid, missing, or not authorized."""

    def __init__(
        self, message="Authentication failed. Check your API key and permissions."
    ):
        super().__init__(message)


class InvalidInputError(MoorchehError):
    """
    Raised for client-side errors like invalid parameters
    or request body (400 Bad Request).
    """

    def __init__(self, message="Invalid input provided."):
        super().__init__(message)


class NamespaceNotFound(MoorchehError):
    """Raised when a specified namespace cannot be found (404 Not Found)."""

    def __init__(self, namespace_name: str, message: str | None = None):
        self.namespace_name = namespace_name
        if message is None:
            message = f"Namespace '{namespace_name}' not found."
        super().__init__(message)


class ConflictError(MoorchehError):
    """Raised when an operation conflicts with the current state (409 Conflict)."""

    def __init__(self, message="Operation conflict."):
        super().__init__(message)


class APIError(MoorchehError):
    """Raised for general server-side API errors (5xx) or unexpected responses."""

    def __init__(
        self, status_code: int | None = None, message="An API error occurred."
    ):
        self.status_code = status_code
        full_message = (
            f"API Error (Status: {status_code}): {message}" if status_code else message
        )
        super().__init__(full_message)


# Add more specific exceptions as needed
