"""
pyjoy.evaluator.logic - Comparison and boolean primitives.

Contains: <, >, <=, >=, =, !=, equal, compare, and, or, not, xor
"""

from __future__ import annotations

import struct
from typing import Any

from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyQuotation, JoyType, JoyValue

from .core import joy_word


def _float_to_bits(f: float) -> int:
    """Convert float to its IEEE 754 double-precision bit representation."""
    return struct.unpack(">Q", struct.pack(">d", f))[0]


def _numeric_value(v: JoyValue) -> int | float | None:
    """Extract numeric value for comparison.

    Joy treats many types as having numeric interpretations:
    - INTEGER/FLOAT: direct value
    - CHAR: ordinal value
    - BOOLEAN: 1 for true, 0 for false
    - SET: bitset integer (sum of 2^n for each n in set)
    - LIST/QUOTATION: 0 if empty, otherwise not comparable numerically
    - STRING: 0 if empty, otherwise not comparable numerically
    - FILE: 0 (files compare equal to empty/false in =)
    - SYMBOL: not comparable numerically
    """
    if v.type == JoyType.INTEGER:
        return v.value
    elif v.type == JoyType.FLOAT:
        return v.value
    elif v.type == JoyType.CHAR:
        return ord(v.value)
    elif v.type == JoyType.BOOLEAN:
        return 1 if v.value else 0
    elif v.type == JoyType.SET:
        # Set is a bitset - convert to integer
        return sum(1 << n for n in v.value)
    elif v.type in (JoyType.LIST, JoyType.QUOTATION):
        # Empty list/quotation equals 0
        items = v.value if v.type == JoyType.LIST else v.value.terms
        return 0 if len(items) == 0 else None  # None means not comparable
    elif v.type == JoyType.STRING:
        # Empty string equals 0
        return 0 if len(v.value) == 0 else None
    elif v.type == JoyType.FILE:
        # Failed file open (None value) equals 0
        # Valid file handles are not numerically comparable
        return 0 if v.value is None else None
    else:
        return None  # Not numerically comparable


# -----------------------------------------------------------------------------
# Comparison Operations
# -----------------------------------------------------------------------------


def _can_compare_numerically(a: JoyValue, b: JoyValue) -> tuple[bool, Any, Any]:
    """Check if two values can be compared and return their comparable values."""
    av = _numeric_value(a)
    bv = _numeric_value(b)
    if av is not None and bv is not None:
        return True, av, bv

    # String comparison (including symbol as string)
    a_str = None
    b_str = None
    if a.type == JoyType.STRING:
        a_str = a.value
    elif a.type == JoyType.SYMBOL:
        a_str = a.value
    if b.type == JoyType.STRING:
        b_str = b.value
    elif b.type == JoyType.SYMBOL:
        b_str = b.value

    if a_str is not None and b_str is not None:
        return True, a_str, b_str

    # File comparison by id
    if a.type == JoyType.FILE and b.type == JoyType.FILE:
        return True, id(a.value), id(b.value)

    return False, None, None


@joy_word(name="<", params=2, doc="X Y -> B")
def lt(ctx: ExecutionContext) -> None:
    """Less than."""
    b, a = ctx.stack.pop_n(2)
    can_cmp, av, bv = _can_compare_numerically(a, b)
    if can_cmp:
        result = av < bv
    else:
        result = False
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name=">", params=2, doc="X Y -> B")
def gt(ctx: ExecutionContext) -> None:
    """Greater than."""
    b, a = ctx.stack.pop_n(2)
    can_cmp, av, bv = _can_compare_numerically(a, b)
    if can_cmp:
        result = av > bv
    else:
        result = False
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="<=", params=2, doc="X Y -> B")
def le(ctx: ExecutionContext) -> None:
    """Less than or equal."""
    b, a = ctx.stack.pop_n(2)
    can_cmp, av, bv = _can_compare_numerically(a, b)
    if can_cmp:
        result = av <= bv
    else:
        result = False
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name=">=", params=2, doc="X Y -> B")
def ge(ctx: ExecutionContext) -> None:
    """Greater than or equal."""
    b, a = ctx.stack.pop_n(2)
    can_cmp, av, bv = _can_compare_numerically(a, b)
    if can_cmp:
        result = av >= bv
    else:
        result = False
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="=", params=2, doc="X Y -> B")
def eq(ctx: ExecutionContext) -> None:
    """Equal - Joy's liberal equality comparison.

    In Joy, = compares values with type coercion:
    - Numeric types (int, float, char, bool, set, empty list) compare by value
    - Strings compare by content
    - Symbols compare with their string names
    - Non-empty lists/quotations are only equal to themselves
    """
    b, a = ctx.stack.pop_n(2)
    result = _joy_equals(a, b)
    ctx.stack.push_value(JoyValue.boolean(result))


def _joy_equals(a: JoyValue, b: JoyValue) -> bool:
    """Joy's = equality semantics.

    Key insight: Joy's = is NOT structural equality for aggregates.
    - Non-empty lists/quotations are NEVER equal with = (use 'equal' for that)
    - Empty lists equal 0 and each other
    - Strings compare by content
    - Symbols compare with their string names
    - Numeric types compare by value
    - FLOAT vs SET: compares IEEE 754 bit representation
    """
    # Non-empty lists/quotations are never equal with =
    if a.type in (JoyType.LIST, JoyType.QUOTATION):
        items_a = a.value if a.type == JoyType.LIST else a.value.terms
        if len(items_a) > 0:
            return False  # Non-empty aggregates never equal
    if b.type in (JoyType.LIST, JoyType.QUOTATION):
        items_b = b.value if b.type == JoyType.LIST else b.value.terms
        if len(items_b) > 0:
            return False  # Non-empty aggregates never equal

    # Symbol comparison
    if a.type == JoyType.SYMBOL and b.type == JoyType.SYMBOL:
        return a.value == b.value

    # Symbol compared with string - check if symbol name matches string
    if a.type == JoyType.SYMBOL and b.type == JoyType.STRING:
        return a.value == b.value
    if a.type == JoyType.STRING and b.type == JoyType.SYMBOL:
        return a.value == b.value

    # String comparison
    if a.type == JoyType.STRING and b.type == JoyType.STRING:
        return a.value == b.value

    # FLOAT vs SET: compare IEEE 754 bit representation
    # Joy treats sets as bit patterns; floats compare by their bit representation
    if a.type == JoyType.FLOAT and b.type == JoyType.SET:
        float_bits = _float_to_bits(a.value)
        set_bits = sum(1 << n for n in b.value)
        return float_bits == set_bits
    if a.type == JoyType.SET and b.type == JoyType.FLOAT:
        set_bits = sum(1 << n for n in a.value)
        float_bits = _float_to_bits(b.value)
        return set_bits == float_bits

    # Try numeric comparison (handles int, float, char, bool, set, empty list)
    av = _numeric_value(a)
    bv = _numeric_value(b)
    if av is not None and bv is not None:
        return av == bv

    # Non-comparable types
    return False


@joy_word(name="!=", params=2, doc="X Y -> B")
def ne(ctx: ExecutionContext) -> None:
    """Not equal."""
    b, a = ctx.stack.pop_n(2)
    result = not _joy_equals(a, b)
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="equal", params=2, doc="T U -> B")
def equal(ctx: ExecutionContext) -> None:
    """Recursively test whether trees T and U are identical."""
    b, a = ctx.stack.pop_n(2)
    result = _values_equal(a, b)
    ctx.stack.push_value(JoyValue.boolean(result))


def _values_equal(a: JoyValue, b: JoyValue) -> bool:
    """Deep equality comparison that handles LIST/QUOTATION interop.

    Unlike '=' which treats non-empty lists as never equal,
    'equal' does recursive structural comparison.
    """
    # Same type - direct comparison
    if a.type == b.type:
        if a.type in (JoyType.LIST, JoyType.QUOTATION):
            a_items = a.value if a.type == JoyType.LIST else a.value.terms
            b_items = b.value if b.type == JoyType.LIST else b.value.terms
            if len(a_items) != len(b_items):
                return False
            return all(
                _values_equal(_to_joy_value(x), _to_joy_value(y))
                for x, y in zip(a_items, b_items)
            )
        return a == b

    # LIST and QUOTATION can be compared by content
    if {a.type, b.type} == {JoyType.LIST, JoyType.QUOTATION}:
        a_items = a.value if a.type == JoyType.LIST else a.value.terms
        b_items = b.value if b.type == JoyType.LIST else b.value.terms
        if len(a_items) != len(b_items):
            return False
        return all(
            _values_equal(_to_joy_value(x), _to_joy_value(y))
            for x, y in zip(a_items, b_items)
        )

    # Symbol comparison
    if a.type == JoyType.SYMBOL and b.type == JoyType.SYMBOL:
        return a.value == b.value

    # Try numeric comparison (int, float, char, bool, set, empty list)
    av = _numeric_value(a)
    bv = _numeric_value(b)
    if av is not None and bv is not None:
        return av == bv

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
    """Compare A and B, return -1, 0, or 1.

    Joy compare semantics:
    - Numeric types (int, float, char, bool, set): compare by value
    - Strings: lexicographic comparison
    - Symbols: 0 if same, 1 if different
    - Lists/Quotations: always 1 (not comparable)
    - Files: compare by identity/order
    - Different incompatible types: 1
    """
    b, a = ctx.stack.pop_n(2)
    result = _joy_compare(a, b)
    ctx.stack.push_value(JoyValue.integer(result))


def _joy_compare(a: JoyValue, b: JoyValue) -> int:
    """Joy compare implementation returning -1, 0, or 1."""
    # Non-empty lists/quotations are not comparable - always return 1
    if a.type in (JoyType.LIST, JoyType.QUOTATION):
        items_a = a.value if a.type == JoyType.LIST else a.value.terms
        if len(items_a) > 0:
            return 1
    if b.type in (JoyType.LIST, JoyType.QUOTATION):
        items_b = b.value if b.type == JoyType.LIST else b.value.terms
        if len(items_b) > 0:
            return 1

    # String comparison (lexicographic)
    if a.type == JoyType.STRING and b.type == JoyType.STRING:
        if a.value < b.value:
            return -1
        elif a.value > b.value:
            return 1
        return 0

    # Symbol comparison
    if a.type == JoyType.SYMBOL and b.type == JoyType.SYMBOL:
        return 0 if a.value == b.value else 1

    # File comparison
    if a.type == JoyType.FILE and b.type == JoyType.FILE:
        # Compare by file object identity or name
        if a.value == b.value:
            return 0
        # Use id for ordering
        return -1 if id(a.value) < id(b.value) else 1

    # Try numeric comparison
    av = _numeric_value(a)
    bv = _numeric_value(b)
    if av is not None and bv is not None:
        if av < bv:
            return -1
        elif av > bv:
            return 1
        return 0

    # Incompatible types - return 1
    return 1


# -----------------------------------------------------------------------------
# Boolean Operations
# -----------------------------------------------------------------------------


@joy_word(name="and", params=2, doc="B1 B2 -> B | S1 S2 -> S")
def and_word(ctx: ExecutionContext) -> None:
    """Logical and, or set intersection."""
    b, a = ctx.stack.pop_n(2)
    # Set intersection
    if a.type == JoyType.SET and b.type == JoyType.SET:
        result = a.value & b.value
        ctx.stack.push_value(JoyValue.joy_set(result))
    else:
        result = a.is_truthy() and b.is_truthy()
        ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="or", params=2, doc="B1 B2 -> B | S1 S2 -> S")
def or_word(ctx: ExecutionContext) -> None:
    """Logical or, or set union."""
    b, a = ctx.stack.pop_n(2)
    # Set union
    if a.type == JoyType.SET and b.type == JoyType.SET:
        result = a.value | b.value
        ctx.stack.push_value(JoyValue.joy_set(result))
    else:
        result = a.is_truthy() or b.is_truthy()
        ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="not", params=1, doc="B -> B | S -> S")
def not_word(ctx: ExecutionContext) -> None:
    """Logical not, or set complement."""
    a = ctx.stack.pop()
    # Set complement (all 64 possible members minus current)
    if a.type == JoyType.SET:
        all_members = frozenset(range(64))
        result = all_members - a.value
        ctx.stack.push_value(JoyValue.joy_set(result))
    else:
        result = not a.is_truthy()
        ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="xor", params=2, doc="B1 B2 -> B | S1 S2 -> S")
def xor_word(ctx: ExecutionContext) -> None:
    """Logical exclusive or, or set symmetric difference."""
    b, a = ctx.stack.pop_n(2)
    # Set symmetric difference
    if a.type == JoyType.SET and b.type == JoyType.SET:
        result = a.value ^ b.value
        ctx.stack.push_value(JoyValue.joy_set(result))
    else:
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
