"""
Tests for pyjoy.stack module.
"""

import pytest

from pyjoy.errors import JoyStackUnderflow
from pyjoy.stack import JoyStack
from pyjoy.types import JoyType, JoyValue


class TestJoyStack:
    """Tests for JoyStack operations."""

    def test_empty_stack(self, stack):
        assert stack.depth == 0
        assert stack.is_empty()

    def test_push_integer(self, stack):
        stack.push(42)
        assert stack.depth == 1
        assert stack.peek().type == JoyType.INTEGER
        assert stack.peek().value == 42

    def test_push_converts_to_joyvalue(self, stack):
        stack.push(42)
        assert isinstance(stack.peek(), JoyValue)

    def test_push_value_direct(self, stack):
        v = JoyValue.integer(42)
        stack.push_value(v)
        assert stack.peek() is v

    def test_pop(self, stack):
        stack.push(42)
        v = stack.pop()
        assert v.value == 42
        assert stack.is_empty()

    def test_pop_empty_raises(self, stack):
        with pytest.raises(JoyStackUnderflow):
            stack.pop()

    def test_peek_depth(self, stack):
        stack.push(1)
        stack.push(2)
        stack.push(3)
        assert stack.peek(0).value == 3  # TOS
        assert stack.peek(1).value == 2
        assert stack.peek(2).value == 1

    def test_peek_too_deep_raises(self, stack):
        stack.push(1)
        with pytest.raises(JoyStackUnderflow):
            stack.peek(1)

    def test_pop_n(self, stack):
        stack.push(1)
        stack.push(2)
        stack.push(3)
        result = stack.pop_n(2)
        # TOS first
        assert result[0].value == 3
        assert result[1].value == 2
        assert stack.depth == 1

    def test_pop_n_empty(self, stack):
        result = stack.pop_n(0)
        assert result == ()

    def test_pop_n_underflow(self, stack):
        stack.push(1)
        with pytest.raises(JoyStackUnderflow):
            stack.pop_n(2)

    def test_push_many(self, stack):
        stack.push_many(1, 2, 3)
        assert stack.depth == 3
        assert stack.peek(0).value == 3
        assert stack.peek(2).value == 1

    def test_clear(self, stack):
        stack.push(1)
        stack.push(2)
        stack.clear()
        assert stack.is_empty()

    def test_copy(self, stack):
        stack.push(1)
        stack.push(2)
        copy = stack.copy()
        assert copy.depth == 2
        # Modifying copy doesn't affect original
        copy.pop()
        assert stack.depth == 2

    def test_items(self, stack):
        stack.push(1)
        stack.push(2)
        items = stack.items()
        assert len(items) == 2
        assert items[0].value == 1  # Bottom
        assert items[1].value == 2  # Top

    def test_len(self, stack):
        assert len(stack) == 0
        stack.push(1)
        assert len(stack) == 1


class TestExecutionContext:
    """Tests for ExecutionContext."""

    def test_has_stack(self, ctx):
        assert isinstance(ctx.stack, JoyStack)

    def test_save_restore_stack(self, ctx):
        ctx.stack.push(1)
        ctx.stack.push(2)
        state_id = ctx.save_stack()

        ctx.stack.push(3)
        assert ctx.stack.depth == 3

        ctx.restore_stack(state_id)
        assert ctx.stack.depth == 2
        assert ctx.stack.peek().value == 2

    def test_pop_saved(self, ctx):
        ctx.stack.push(1)
        ctx.save_stack()
        ctx.save_stack()
        assert len(ctx._saved_states) == 2

        ctx.pop_saved()
        assert len(ctx._saved_states) == 1

    def test_get_saved(self, ctx):
        ctx.stack.push(1)
        ctx.stack.push(2)
        state_id = ctx.save_stack()

        # depth 0 = top = 2
        assert ctx.get_saved(state_id, 0).value == 2
        # depth 1 = second = 1
        assert ctx.get_saved(state_id, 1).value == 1
