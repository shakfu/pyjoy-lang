"""
Tests for pyjoy.types module.
"""

import pytest

from pyjoy.errors import JoySetMemberError, JoyTypeError
from pyjoy.types import (
    EMPTY_LIST,
    FALSE,
    TRUE,
    JoyQuotation,
    JoyType,
    JoyValue,
    joy_to_python,
    python_to_joy,
)


class TestJoyValue:
    """Tests for JoyValue creation and methods."""

    def test_integer(self):
        v = JoyValue.integer(42)
        assert v.type == JoyType.INTEGER
        assert v.value == 42
        assert repr(v) == "42"

    def test_negative_integer(self):
        v = JoyValue.integer(-17)
        assert v.type == JoyType.INTEGER
        assert v.value == -17

    def test_float(self):
        v = JoyValue.floating(3.14)
        assert v.type == JoyType.FLOAT
        assert v.value == 3.14

    def test_string(self):
        v = JoyValue.string("hello")
        assert v.type == JoyType.STRING
        assert v.value == "hello"
        assert repr(v) == '"hello"'

    def test_char(self):
        v = JoyValue.char("x")
        assert v.type == JoyType.CHAR
        assert v.value == "x"
        assert repr(v) == "'x'"

    def test_char_invalid_length(self):
        with pytest.raises(ValueError):
            JoyValue.char("ab")

    def test_boolean_true(self):
        v = JoyValue.boolean(True)
        assert v.type == JoyType.BOOLEAN
        assert v.value is True
        assert repr(v) == "true"

    def test_boolean_false(self):
        v = JoyValue.boolean(False)
        assert v.type == JoyType.BOOLEAN
        assert v.value is False
        assert repr(v) == "false"

    def test_list(self):
        items = (JoyValue.integer(1), JoyValue.integer(2), JoyValue.integer(3))
        v = JoyValue.list(items)
        assert v.type == JoyType.LIST
        assert len(v.value) == 3
        assert repr(v) == "[1 2 3]"

    def test_empty_list(self):
        v = JoyValue.list(())
        assert v.type == JoyType.LIST
        assert v.value == ()
        assert repr(v) == "[]"

    def test_set(self):
        v = JoyValue.joy_set(frozenset({0, 1, 2}))
        assert v.type == JoyType.SET
        assert v.value == frozenset({0, 1, 2})
        assert repr(v) == "{0 1 2}"

    def test_set_invalid_member(self):
        with pytest.raises(JoySetMemberError):
            JoyValue.joy_set(frozenset({64}))

    def test_set_negative_invalid(self):
        with pytest.raises(JoySetMemberError):
            JoyValue.joy_set(frozenset({-1}))


class TestJoyQuotation:
    """Tests for JoyQuotation."""

    def test_empty_quotation(self):
        q = JoyQuotation(())
        assert len(q) == 0
        assert repr(q) == "[]"

    def test_quotation_with_values(self):
        q = JoyQuotation((JoyValue.integer(1), JoyValue.integer(2)))
        assert len(q) == 2
        assert repr(q) == "[1 2]"

    def test_quotation_with_symbols(self):
        q = JoyQuotation(("dup", "*"))
        assert len(q) == 2
        assert repr(q) == "[dup *]"

    def test_quotation_iteration(self):
        q = JoyQuotation((JoyValue.integer(1), JoyValue.integer(2)))
        items = list(q)
        assert len(items) == 2

    def test_quotation_equality(self):
        q1 = JoyQuotation((JoyValue.integer(1),))
        q2 = JoyQuotation((JoyValue.integer(1),))
        assert q1 == q2


class TestPythonToJoy:
    """Tests for python_to_joy conversion."""

    def test_int(self):
        v = python_to_joy(42)
        assert v.type == JoyType.INTEGER
        assert v.value == 42

    def test_float(self):
        v = python_to_joy(3.14)
        assert v.type == JoyType.FLOAT

    def test_bool_true(self):
        v = python_to_joy(True)
        assert v.type == JoyType.BOOLEAN
        assert v.value is True

    def test_bool_false(self):
        v = python_to_joy(False)
        assert v.type == JoyType.BOOLEAN
        assert v.value is False

    def test_string(self):
        v = python_to_joy("hello")
        assert v.type == JoyType.STRING

    def test_single_char_is_char(self):
        v = python_to_joy("x")
        assert v.type == JoyType.CHAR

    def test_list(self):
        v = python_to_joy([1, 2, 3])
        assert v.type == JoyType.LIST
        assert len(v.value) == 3

    def test_tuple(self):
        v = python_to_joy((1, 2))
        assert v.type == JoyType.LIST

    def test_frozenset(self):
        v = python_to_joy(frozenset({0, 1, 2}))
        assert v.type == JoyType.SET

    def test_joyvalue_passthrough(self):
        original = JoyValue.integer(42)
        v = python_to_joy(original)
        assert v is original

    def test_unconvertible_type(self):
        with pytest.raises(JoyTypeError):
            python_to_joy({"key": "value"})


class TestJoyToPython:
    """Tests for joy_to_python conversion."""

    def test_integer(self):
        v = JoyValue.integer(42)
        assert joy_to_python(v) == 42

    def test_list(self):
        v = JoyValue.list((JoyValue.integer(1), JoyValue.integer(2)))
        result = joy_to_python(v)
        assert result == (1, 2)


class TestTypeHelpers:
    """Tests for JoyValue helper methods."""

    def test_is_numeric(self):
        assert JoyValue.integer(1).is_numeric()
        assert JoyValue.floating(1.0).is_numeric()
        assert not JoyValue.string("x").is_numeric()

    def test_is_aggregate(self):
        assert JoyValue.list(()).is_aggregate()
        assert JoyValue.string("x").is_aggregate()
        assert JoyValue.joy_set(frozenset()).is_aggregate()
        assert not JoyValue.integer(1).is_aggregate()

    def test_is_truthy(self):
        assert JoyValue.boolean(True).is_truthy()
        assert not JoyValue.boolean(False).is_truthy()
        assert JoyValue.integer(1).is_truthy()
        assert not JoyValue.integer(0).is_truthy()
        assert JoyValue.string("x").is_truthy()
        assert not JoyValue.string("").is_truthy()


class TestSingletons:
    """Tests for singleton values."""

    def test_true_false(self):
        assert TRUE.value is True
        assert FALSE.value is False

    def test_empty_list(self):
        assert EMPTY_LIST.type == JoyType.LIST
        assert EMPTY_LIST.value == ()
