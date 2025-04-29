# tests/test_exceptions.py

import pytest
from moorcheh_sdk.exceptions import (
    MoorchehError,
    AuthenticationError,
    InvalidInputError,
    NamespaceNotFound,
    ConflictError,
    APIError,
)

# --- Test MoorchehError (Base Exception) ---

def test_moorcheh_error_inheritance():
    """Verify MoorchehError inherits from Exception."""
    assert issubclass(MoorchehError, Exception)

def test_moorcheh_error_default_message():
    """Test the default message of MoorchehError."""
    try:
        raise MoorchehError()
    except MoorchehError as e:
        assert e.message == "An unspecified error occurred with the Moorcheh SDK"
        assert str(e) == "An unspecified error occurred with the Moorcheh SDK"

def test_moorcheh_error_custom_message():
    """Test MoorchehError with a custom message."""
    custom_msg = "A specific SDK error happened."
    try:
        raise MoorchehError(custom_msg)
    except MoorchehError as e:
        assert e.message == custom_msg
        assert str(e) == custom_msg

# --- Test AuthenticationError ---

def test_authentication_error_inheritance():
    """Verify AuthenticationError inherits from MoorchehError."""
    assert issubclass(AuthenticationError, MoorchehError)

def test_authentication_error_default_message():
    """Test the default message of AuthenticationError."""
    try:
        raise AuthenticationError()
    except AuthenticationError as e:
        assert e.message == "Authentication failed. Check your API key and permissions."
        assert str(e) == "Authentication failed. Check your API key and permissions."

def test_authentication_error_custom_message():
    """Test AuthenticationError with a custom message."""
    custom_msg = "API key expired."
    try:
        raise AuthenticationError(custom_msg)
    except AuthenticationError as e:
        assert e.message == custom_msg
        assert str(e) == custom_msg

# --- Test InvalidInputError ---

def test_invalid_input_error_inheritance():
    """Verify InvalidInputError inherits from MoorchehError."""
    assert issubclass(InvalidInputError, MoorchehError)

def test_invalid_input_error_default_message():
    """Test the default message of InvalidInputError."""
    try:
        raise InvalidInputError()
    except InvalidInputError as e:
        assert e.message == "Invalid input provided."
        assert str(e) == "Invalid input provided."

def test_invalid_input_error_custom_message():
    """Test InvalidInputError with a custom message."""
    custom_msg = "Parameter 'top_k' must be positive."
    try:
        raise InvalidInputError(custom_msg)
    except InvalidInputError as e:
        assert e.message == custom_msg
        assert str(e) == custom_msg

# --- Test NamespaceNotFound ---

def test_namespace_not_found_error_inheritance():
    """Verify NamespaceNotFound inherits from MoorchehError."""
    assert issubclass(NamespaceNotFound, MoorchehError)

def test_namespace_not_found_error_default_message():
    """Test the default message and attribute of NamespaceNotFound."""
    ns_name = "my-missing-ns"
    try:
        raise NamespaceNotFound(namespace_name=ns_name)
    except NamespaceNotFound as e:
        expected_msg = f"Namespace '{ns_name}' not found."
        assert e.message == expected_msg
        assert str(e) == expected_msg
        assert e.namespace_name == ns_name

def test_namespace_not_found_error_custom_message():
    """Test NamespaceNotFound with a custom message."""
    ns_name = "another-ns"
    custom_msg = f"Could not find the namespace named '{ns_name}' during search."
    try:
        raise NamespaceNotFound(namespace_name=ns_name, message=custom_msg)
    except NamespaceNotFound as e:
        assert e.message == custom_msg
        assert str(e) == custom_msg
        assert e.namespace_name == ns_name # Attribute should still be set

# --- Test ConflictError ---

def test_conflict_error_inheritance():
    """Verify ConflictError inherits from MoorchehError."""
    assert issubclass(ConflictError, MoorchehError)

def test_conflict_error_default_message():
    """Test the default message of ConflictError."""
    try:
        raise ConflictError()
    except ConflictError as e:
        assert e.message == "Operation conflict."
        assert str(e) == "Operation conflict."

def test_conflict_error_custom_message():
    """Test ConflictError with a custom message."""
    custom_msg = "Namespace 'existing-ns' already exists."
    try:
        raise ConflictError(custom_msg)
    except ConflictError as e:
        assert e.message == custom_msg
        assert str(e) == custom_msg

# --- Test APIError ---

def test_api_error_inheritance():
    """Verify APIError inherits from MoorchehError."""
    assert issubclass(APIError, MoorchehError)

def test_api_error_default_message():
    """Test the default message of APIError when no status code is given."""
    try:
        raise APIError()
    except APIError as e:
        assert e.message == "An API error occurred."
        assert str(e) == "An API error occurred."
        assert e.status_code is None

def test_api_error_custom_message_no_status():
    """Test APIError with a custom message and no status code."""
    custom_msg = "Unexpected response structure received from server."
    try:
        raise APIError(message=custom_msg)
    except APIError as e:
        assert e.message == custom_msg
        assert str(e) == custom_msg
        assert e.status_code is None

def test_api_error_with_status_code_and_default_message():
    """Test APIError with a status code and the default message part."""
    status = 500
    try:
        raise APIError(status_code=status)
    except APIError as e:
        expected_msg = f"API Error (Status: {status}): An API error occurred."
        assert e.message == expected_msg # The full message including status
        assert str(e) == expected_msg
        assert e.status_code == status

def test_api_error_with_status_code_and_custom_message():
    """Test APIError with both status code and a custom message."""
    status = 400
    custom_msg = "Invalid request payload."
    try:
        raise APIError(status_code=status, message=custom_msg)
    except APIError as e:
        expected_msg = f"API Error (Status: {status}): {custom_msg}"
        assert e.message == expected_msg # The full message including status
        assert str(e) == expected_msg
        assert e.status_code == status

