"""
Tests for pyjoy.evaluator module.
"""

import pytest

from pyjoy.errors import JoyStackUnderflow, JoyTypeError, JoyUndefinedWord
from pyjoy.evaluator import get_primitive, list_primitives
from pyjoy.types import JoyQuotation, JoyType, JoyValue


class TestEvaluator:
    """Tests for the Joy evaluator."""

    def test_push_integer(self, evaluator):
        evaluator.run("42")
        assert evaluator.stack.depth == 1
        assert evaluator.stack.peek().value == 42

    def test_push_multiple(self, evaluator):
        evaluator.run("1 2 3")
        assert evaluator.stack.depth == 3
        assert evaluator.stack.peek().value == 3

    def test_push_float(self, evaluator):
        evaluator.run("3.14")
        assert evaluator.stack.peek().type == JoyType.FLOAT

    def test_push_string(self, evaluator):
        evaluator.run('"hello"')
        assert evaluator.stack.peek().type == JoyType.STRING
        assert evaluator.stack.peek().value == "hello"

    def test_push_boolean(self, evaluator):
        evaluator.run("true false")
        assert evaluator.stack.peek(0).value is False
        assert evaluator.stack.peek(1).value is True

    def test_push_quotation(self, evaluator):
        evaluator.run("[1 2 3]")
        assert evaluator.stack.depth == 1
        v = evaluator.stack.peek()
        assert v.type == JoyType.QUOTATION
        assert len(v.value.terms) == 3

    def test_push_set(self, evaluator):
        evaluator.run("{0 1 2}")
        assert evaluator.stack.peek().type == JoyType.SET

    def test_undefined_word_raises(self, evaluator):
        with pytest.raises(JoyUndefinedWord):
            evaluator.run("undefined_word_xyz")


class TestStackPrimitives:
    """Tests for stack manipulation primitives."""

    def test_dup(self, evaluator):
        evaluator.run("42 dup")
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == 42
        assert evaluator.stack.peek(1).value == 42

    def test_dup_underflow(self, evaluator):
        with pytest.raises(JoyStackUnderflow):
            evaluator.run("dup")

    def test_pop(self, evaluator):
        evaluator.run("1 2 pop")
        assert evaluator.stack.depth == 1
        assert evaluator.stack.peek().value == 1

    def test_pop_underflow(self, evaluator):
        with pytest.raises(JoyStackUnderflow):
            evaluator.run("pop")

    def test_swap(self, evaluator):
        evaluator.run("1 2 swap")
        assert evaluator.stack.peek(0).value == 1
        assert evaluator.stack.peek(1).value == 2

    def test_swap_underflow(self, evaluator):
        evaluator.run("1")
        with pytest.raises(JoyStackUnderflow):
            evaluator.run("swap")


class TestQuotationExecution:
    """Tests for quotation execution."""

    def test_i_combinator(self, evaluator):
        evaluator.run("42 [dup] i")
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == 42
        assert evaluator.stack.peek(1).value == 42

    def test_i_type_error(self, evaluator):
        evaluator.run("42")
        with pytest.raises(JoyTypeError):
            evaluator.run("i")

    def test_nested_quotation_execution(self, evaluator):
        evaluator.run("1 [[2] i] i")
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == 2
        assert evaluator.stack.peek(1).value == 1


class TestUserDefinitions:
    """Tests for user-defined words."""

    def test_define_and_call(self, evaluator):
        evaluator.define("double", JoyQuotation(("dup", "+")))
        # Note: + is not defined yet, so this would fail
        # For now, just test definition storage
        assert "double" in evaluator.definitions

    def test_definition_lookup(self, evaluator):
        # Define a word that just pushes 42
        evaluator.define("answer", JoyQuotation((JoyValue.integer(42),)))
        evaluator.run("answer")
        assert evaluator.stack.peek().value == 42


class TestPrimitiveRegistry:
    """Tests for primitive registration."""

    def test_list_primitives(self):
        prims = list_primitives()
        assert "dup" in prims
        assert "pop" in prims
        assert "swap" in prims
        assert "i" in prims

    def test_get_primitive(self):
        dup = get_primitive("dup")
        assert dup is not None
        assert callable(dup)

    def test_get_nonexistent(self):
        assert get_primitive("nonexistent_xyz") is None


class TestStackWord:
    """Tests for stack introspection."""

    def test_stack_word(self, evaluator):
        evaluator.run("1 2 3 stack")
        # Stack should now have: 1 2 3 [1 2 3]
        assert evaluator.stack.depth == 4
        top = evaluator.stack.peek()
        assert top.type == JoyType.LIST
        assert len(top.value) == 3

    def test_unstack_word(self, evaluator):
        evaluator.run("[1 2 3] unstack")
        assert evaluator.stack.depth == 3
        assert evaluator.stack.peek(0).value == 3
        assert evaluator.stack.peek(1).value == 2
        assert evaluator.stack.peek(2).value == 1
