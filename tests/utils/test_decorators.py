import pytest

from moorcheh_sdk.exceptions import InvalidInputError
from moorcheh_sdk.utils.decorators import required_args


class TestClass:
    @required_args(["a", "b"], types={"a": int, "b": str})
    def method(self, a, b, c=None):
        return a, b, c


def test_required_args_success():
    """Test that the decorator allows valid arguments."""
    obj = TestClass()
    assert obj.method(1, "test") == (1, "test", None)
    assert obj.method(a=1, b="test", c="optional") == (1, "test", "optional")


def test_required_args_missing_arg():
    """Test that missing required arguments raise TypeError (caught and re-raised as InvalidInputError)."""
    obj = TestClass()
    # If an argument is missing from the call, python's bind will raise TypeError
    with pytest.raises(InvalidInputError):
        obj.method(a=1)


def test_required_args_none_value():
    """Test that None values for required arguments raise InvalidInputError."""
    obj = TestClass()
    with pytest.raises(InvalidInputError, match="Argument 'a' cannot be None."):
        obj.method(a=None, b="test")

    with pytest.raises(InvalidInputError, match="Argument 'b' cannot be None."):
        obj.method(a=1, b=None)


def test_required_args_empty_value():
    """Test that empty values for string/list arguments raise InvalidInputError."""
    obj = TestClass()
    with pytest.raises(InvalidInputError, match="Argument 'b' cannot be empty."):
        obj.method(a=1, b="")


def test_required_args_wrong_type():
    """Test that arguments with wrong types raise InvalidInputError."""
    obj = TestClass()
    with pytest.raises(
        InvalidInputError, match="Argument 'a' must be of type <class 'int'>."
    ):
        obj.method(a="not an int", b="test")

    with pytest.raises(
        InvalidInputError, match="Argument 'b' must be of type <class 'str'>."
    ):
        obj.method(a=1, b=123)


def test_required_args_allow_zero_false():
    """Test that 0 and False are not considered empty."""

    @required_args(["num", "flag"], types={"num": int, "flag": bool})
    def func(num, flag):
        return num, flag

    assert func(0, False) == (0, False)


def test_required_args_list_validation():
    """Test validation for list types."""

    @required_args(["items"], types={"items": list})
    def func(items):
        return items

    assert func([1, 2]) == [1, 2]

    with pytest.raises(InvalidInputError, match="Argument 'items' cannot be empty."):
        func([])

    with pytest.raises(
        InvalidInputError, match="Argument 'items' must be of type <class 'list'>."
    ):
        func("not a list")
