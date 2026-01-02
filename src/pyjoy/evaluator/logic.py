"""
pyjoy.evaluator.logic - Comparison and boolean primitives.

Contains: <, >, <=, >=, =, !=, equal, compare, and, or, not, xor
"""

from __future__ import annotations

from typing import Any

from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyQuotation, JoyType, JoyValue

from .core import joy_word


def _numeric_value(v: JoyValue) -> int | float:
    """Extract numeric value for comparison."""
    if v.type == JoyType.INTEGER:
        return v.value
    elif v.type == JoyType.FLOAT:
        return v.value
    elif v.type == JoyType.CHAR:
        return ord(v.value)
    elif v.type == JoyType.BOOLEAN:
        return 1 if v.value else 0
    else:
        return 0


# -----------------------------------------------------------------------------
# Comparison Operations
# -----------------------------------------------------------------------------


@joy_word(name="<", params=2, doc="X Y -> B")
def lt(ctx: ExecutionContext) -> None:
    """Less than."""
    b, a = ctx.stack.pop_n(2)
    result = _numeric_value(a) < _numeric_value(b)
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name=">", params=2, doc="X Y -> B")
def gt(ctx: ExecutionContext) -> None:
    """Greater than."""
    b, a = ctx.stack.pop_n(2)
    result = _numeric_value(a) > _numeric_value(b)
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="<=", params=2, doc="X Y -> B")
def le(ctx: ExecutionContext) -> None:
    """Less than or equal."""
    b, a = ctx.stack.pop_n(2)
    result = _numeric_value(a) <= _numeric_value(b)
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name=">=", params=2, doc="X Y -> B")
def ge(ctx: ExecutionContext) -> None:
    """Greater than or equal."""
    b, a = ctx.stack.pop_n(2)
    result = _numeric_value(a) >= _numeric_value(b)
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="=", params=2, doc="X Y -> B")
def eq(ctx: ExecutionContext) -> None:
    """Equal (structural equality)."""
    b, a = ctx.stack.pop_n(2)
    # For numeric types, compare values
    if a.is_numeric() and b.is_numeric():
        result = _numeric_value(a) == _numeric_value(b)
    else:
        # Structural equality
        result = a == b
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="!=", params=2, doc="X Y -> B")
def ne(ctx: ExecutionContext) -> None:
    """Not equal."""
    b, a = ctx.stack.pop_n(2)
    if a.is_numeric() and b.is_numeric():
        result = _numeric_value(a) != _numeric_value(b)
    else:
        result = a != b
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="equal", params=2, doc="T U -> B")
def equal(ctx: ExecutionContext) -> None:
    """Recursively test whether trees T and U are identical."""
    b, a = ctx.stack.pop_n(2)
    result = _values_equal(a, b)
    ctx.stack.push_value(JoyValue.boolean(result))


def _values_equal(a: JoyValue, b: JoyValue) -> bool:
    """Deep equality comparison that handles LIST/QUOTATION interop."""
    # Same type - direct comparison
    if a.type == b.type:
        if a.type in (JoyType.LIST, JoyType.QUOTATION):
            a_items = a.value if a.type == JoyType.LIST else a.value.terms
            b_items = b.value if b.type == JoyType.LIST else b.value.terms
            if len(a_items) != len(b_items):
                return False
            return all(_values_equal(_to_joy_value(x), _to_joy_value(y))
                      for x, y in zip(a_items, b_items))
        return a == b

    # LIST and QUOTATION can be compared by content
    if {a.type, b.type} == {JoyType.LIST, JoyType.QUOTATION}:
        a_items = a.value if a.type == JoyType.LIST else a.value.terms
        b_items = b.value if b.type == JoyType.LIST else b.value.terms
        if len(a_items) != len(b_items):
            return False
        return all(_values_equal(_to_joy_value(x), _to_joy_value(y))
                  for x, y in zip(a_items, b_items))

    # Numeric types can be compared across int/float
    if a.is_numeric() and b.is_numeric():
        return _numeric_value(a) == _numeric_value(b)

    return False


def _to_joy_value(item: Any) -> JoyValue:
    """Convert an item to JoyValue if needed."""
    if isinstance(item, JoyValue):
        return item
    if isinstance(item, str):
        return JoyValue.symbol(item)
    if isinstance(item, int):
        return JoyValue.integer(item)
    if isinstance(item, float):
        return JoyValue.floating(item)
    if isinstance(item, bool):
        return JoyValue.boolean(item)
    if isinstance(item, JoyQuotation):
        return JoyValue.quotation(item)
    return JoyValue.symbol(str(item))


@joy_word(name="compare", params=2, doc="A B -> I")
def compare(ctx: ExecutionContext) -> None:
    """Compare A and B, return -1, 0, or 1."""
    b, a = ctx.stack.pop_n(2)
    av = _numeric_value(a)
    bv = _numeric_value(b)
    if av < bv:
        result = -1
    elif av > bv:
        result = 1
    else:
        result = 0
    ctx.stack.push_value(JoyValue.integer(result))


# -----------------------------------------------------------------------------
# Boolean Operations
# -----------------------------------------------------------------------------


@joy_word(name="and", params=2, doc="B1 B2 -> B")
def and_word(ctx: ExecutionContext) -> None:
    """Logical and."""
    b, a = ctx.stack.pop_n(2)
    result = a.is_truthy() and b.is_truthy()
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="or", params=2, doc="B1 B2 -> B")
def or_word(ctx: ExecutionContext) -> None:
    """Logical or."""
    b, a = ctx.stack.pop_n(2)
    result = a.is_truthy() or b.is_truthy()
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="not", params=1, doc="B -> B")
def not_word(ctx: ExecutionContext) -> None:
    """Logical not."""
    a = ctx.stack.pop()
    result = not a.is_truthy()
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="xor", params=2, doc="B1 B2 -> B")
def xor_word(ctx: ExecutionContext) -> None:
    """Logical exclusive or."""
    b, a = ctx.stack.pop_n(2)
    result = a.is_truthy() != b.is_truthy()
    ctx.stack.push_value(JoyValue.boolean(result))


# -----------------------------------------------------------------------------
# Boolean Constants
# -----------------------------------------------------------------------------


@joy_word(name="true", params=0, doc="-> B")
def true_(ctx: ExecutionContext) -> None:
    """Push true."""
    ctx.stack.push_value(JoyValue.boolean(True))


@joy_word(name="false", params=0, doc="-> B")
def false_(ctx: ExecutionContext) -> None:
    """Push false."""
    ctx.stack.push_value(JoyValue.boolean(False))
