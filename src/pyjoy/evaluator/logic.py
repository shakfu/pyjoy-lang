"""
pyjoy.evaluator.logic - Comparison and boolean primitives.

Contains: <, >, <=, >=, =, !=, equal, compare, and, or, not, xor
"""

from __future__ import annotations

import struct
from typing import Any

from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyQuotation, JoyType, JoyValue

from .core import is_joy_value, joy_word


def _float_to_bits(f: float) -> int:
    """Convert float to its IEEE 754 double-precision bit representation."""
    return struct.unpack(">Q", struct.pack(">d", f))[0]


def _numeric_value(v: Any) -> int | float | None:
    """Extract numeric value for comparison.

    Works with both JoyValue objects and raw Python values.

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
    # Handle JoyValue objects
    if is_joy_value(v):
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

    # Handle raw Python values (pythonic mode)
    if isinstance(v, bool):
        return 1 if v else 0
    elif isinstance(v, (int, float)):
        return v
    elif isinstance(v, str):
        if len(v) == 1:
            return ord(v)  # Char
        return 0 if len(v) == 0 else None  # String
    elif isinstance(v, frozenset):
        return sum(1 << n for n in v)
    elif isinstance(v, (list, tuple)):
        return 0 if len(v) == 0 else None
    elif isinstance(v, JoyQuotation):
        return 0 if len(v.terms) == 0 else None
    else:
        return None


# -----------------------------------------------------------------------------
# Comparison Operations
# -----------------------------------------------------------------------------


def _can_compare_numerically(a: Any, b: Any) -> tuple[bool, Any, Any]:
    """Check if two values can be compared and return their comparable values.

    Works with both JoyValue objects and raw Python values.
    """
    av = _numeric_value(a)
    bv = _numeric_value(b)
    if av is not None and bv is not None:
        return True, av, bv

    # String comparison (including symbol as string)
    a_str = None
    b_str = None

    if is_joy_value(a):
        if a.type == JoyType.STRING:
            a_str = a.value
        elif a.type == JoyType.SYMBOL:
            a_str = a.value
    elif isinstance(a, str):
        a_str = a

    if is_joy_value(b):
        if b.type == JoyType.STRING:
            b_str = b.value
        elif b.type == JoyType.SYMBOL:
            b_str = b.value
    elif isinstance(b, str):
        b_str = b

    if a_str is not None and b_str is not None:
        return True, a_str, b_str

    # File comparison by id
    if is_joy_value(a) and is_joy_value(b):
        if a.type == JoyType.FILE and b.type == JoyType.FILE:
            return True, id(a.value), id(b.value)

    return False, None, None


def _push_boolean(ctx: ExecutionContext, result: bool) -> None:
    """Push a boolean result in a mode-appropriate way."""
    if ctx.strict:
        ctx.stack.push_value(JoyValue.boolean(result))
    else:
        ctx.stack.push(result)


@joy_word(name="<", params=2, doc="X Y -> B")
def lt(ctx: ExecutionContext) -> None:
    """Less than."""
    b, a = ctx.stack.pop_n(2)
    can_cmp, av, bv = _can_compare_numerically(a, b)
    if can_cmp:
        result = av < bv
    else:
        result = False
    _push_boolean(ctx, result)


@joy_word(name=">", params=2, doc="X Y -> B")
def gt(ctx: ExecutionContext) -> None:
    """Greater than."""
    b, a = ctx.stack.pop_n(2)
    can_cmp, av, bv = _can_compare_numerically(a, b)
    if can_cmp:
        result = av > bv
    else:
        result = False
    _push_boolean(ctx, result)


@joy_word(name="<=", params=2, doc="X Y -> B")
def le(ctx: ExecutionContext) -> None:
    """Less than or equal."""
    b, a = ctx.stack.pop_n(2)
    can_cmp, av, bv = _can_compare_numerically(a, b)
    if can_cmp:
        result = av <= bv
    else:
        result = False
    _push_boolean(ctx, result)


@joy_word(name=">=", params=2, doc="X Y -> B")
def ge(ctx: ExecutionContext) -> None:
    """Greater than or equal."""
    b, a = ctx.stack.pop_n(2)
    can_cmp, av, bv = _can_compare_numerically(a, b)
    if can_cmp:
        result = av >= bv
    else:
        result = False
    _push_boolean(ctx, result)


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
    result = _joy_equals(a, b, ctx.strict)
    _push_boolean(ctx, result)


def _joy_equals(a: Any, b: Any, strict: bool = True) -> bool:
    """Joy's = equality semantics.

    Works with both JoyValue objects and raw Python values.

    Key insight: Joy's = is NOT structural equality for aggregates.
    - Non-empty lists/quotations are NEVER equal with = (use 'equal' for that)
    - Empty lists equal 0 and each other
    - Strings compare by content
    - Symbols compare with their string names
    - Numeric types compare by value
    - FLOAT vs SET: compares IEEE 754 bit representation
    """
    # In pythonic mode with raw values, use simple equality
    if not strict and not is_joy_value(a) and not is_joy_value(b):
        # For raw Python values, use direct comparison
        # But follow Joy semantics for non-empty lists
        if isinstance(a, (list, tuple)) and len(a) > 0:
            return False
        if isinstance(b, (list, tuple)) and len(b) > 0:
            return False
        if isinstance(a, JoyQuotation) and len(a.terms) > 0:
            return False
        if isinstance(b, JoyQuotation) and len(b.terms) > 0:
            return False
        # For numeric comparison
        av = _numeric_value(a)
        bv = _numeric_value(b)
        if av is not None and bv is not None:
            return av == bv
        # String comparison
        if isinstance(a, str) and isinstance(b, str):
            return a == b
        return a == b

    # Handle JoyValue objects (strict mode or mixed)
    if is_joy_value(a):
        # Non-empty lists/quotations are never equal with =
        if a.type in (JoyType.LIST, JoyType.QUOTATION):
            items_a = a.value if a.type == JoyType.LIST else a.value.terms
            if len(items_a) > 0:
                return False  # Non-empty aggregates never equal

    if is_joy_value(b):
        if b.type in (JoyType.LIST, JoyType.QUOTATION):
            items_b = b.value if b.type == JoyType.LIST else b.value.terms
            if len(items_b) > 0:
                return False  # Non-empty aggregates never equal

    # Symbol comparison (JoyValue only)
    if is_joy_value(a) and is_joy_value(b):
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
    result = not _joy_equals(a, b, ctx.strict)
    _push_boolean(ctx, result)


@joy_word(name="equal", params=2, doc="T U -> B")
def equal(ctx: ExecutionContext) -> None:
    """Recursively test whether trees T and U are identical."""
    b, a = ctx.stack.pop_n(2)
    result = _values_equal(a, b, ctx.strict)
    _push_boolean(ctx, result)


def _values_equal(a: Any, b: Any, strict: bool = True) -> bool:
    """Deep equality comparison that handles LIST/QUOTATION interop.

    Works with both JoyValue objects and raw Python values.

    Unlike '=' which treats non-empty lists as never equal,
    'equal' does recursive structural comparison.
    """
    # In pythonic mode with raw values, use simple equality
    if not strict and not is_joy_value(a) and not is_joy_value(b):
        # For raw Python values, do deep comparison
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            if len(a) != len(b):
                return False
            return all(_values_equal(x, y, strict) for x, y in zip(a, b))
        if isinstance(a, JoyQuotation) and isinstance(b, JoyQuotation):
            if len(a.terms) != len(b.terms):
                return False
            return all(_values_equal(x, y, strict) for x, y in zip(a.terms, b.terms))
        return a == b

    # Handle JoyValue objects
    if is_joy_value(a) and is_joy_value(b):
        # Same type - direct comparison
        if a.type == b.type:
            if a.type in (JoyType.LIST, JoyType.QUOTATION):
                a_items = a.value if a.type == JoyType.LIST else a.value.terms
                b_items = b.value if b.type == JoyType.LIST else b.value.terms
                if len(a_items) != len(b_items):
                    return False
                return all(
                    _values_equal(_to_joy_value(x), _to_joy_value(y), strict)
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
                _values_equal(_to_joy_value(x), _to_joy_value(y), strict)
                for x, y in zip(a_items, b_items)
            )

        # Symbol comparison
        if a.type == JoyType.SYMBOL and b.type == JoyType.SYMBOL:
            return a.value == b.value

        # Symbol-String comparison: symbol "foo" equals string "foo"
        if a.type == JoyType.SYMBOL and b.type == JoyType.STRING:
            return a.value == b.value
        if a.type == JoyType.STRING and b.type == JoyType.SYMBOL:
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
    result = _joy_compare(a, b, ctx.strict)
    if ctx.strict:
        ctx.stack.push_value(JoyValue.integer(result))
    else:
        ctx.stack.push(result)


def _joy_compare(a: Any, b: Any, strict: bool = True) -> int:
    """Joy compare implementation returning -1, 0, or 1.

    Works with both JoyValue objects and raw Python values.
    """
    # In pythonic mode with raw values
    if not strict and not is_joy_value(a) and not is_joy_value(b):
        # Non-empty lists are not comparable
        if isinstance(a, (list, tuple)) and len(a) > 0:
            return 1
        if isinstance(b, (list, tuple)) and len(b) > 0:
            return 1
        # Numeric comparison
        av = _numeric_value(a)
        bv = _numeric_value(b)
        if av is not None and bv is not None:
            if av < bv:
                return -1
            elif av > bv:
                return 1
            return 0
        # String comparison
        if isinstance(a, str) and isinstance(b, str):
            if a < b:
                return -1
            elif a > b:
                return 1
            return 0
        return 1  # Incompatible types

    # Handle JoyValue objects
    if is_joy_value(a):
        # Non-empty lists/quotations are not comparable - always return 1
        if a.type in (JoyType.LIST, JoyType.QUOTATION):
            items_a = a.value if a.type == JoyType.LIST else a.value.terms
            if len(items_a) > 0:
                return 1

    if is_joy_value(b):
        if b.type in (JoyType.LIST, JoyType.QUOTATION):
            items_b = b.value if b.type == JoyType.LIST else b.value.terms
            if len(items_b) > 0:
                return 1

    if is_joy_value(a) and is_joy_value(b):
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


def _is_truthy(v: Any) -> bool:
    """Check if a value is truthy in a mode-agnostic way."""
    if is_joy_value(v):
        return v.is_truthy()
    # Raw Python truthiness
    return bool(v)


def _is_set(v: Any) -> bool:
    """Check if a value is a set in a mode-agnostic way."""
    if is_joy_value(v):
        return v.type == JoyType.SET
    return isinstance(v, frozenset)


def _get_set_value(v: Any) -> frozenset:
    """Extract set value in a mode-agnostic way."""
    if is_joy_value(v):
        return v.value
    return v


@joy_word(name="and", params=2, doc="B1 B2 -> B | S1 S2 -> S")
def and_word(ctx: ExecutionContext) -> None:
    """Logical and, or set intersection."""
    b, a = ctx.stack.pop_n(2)
    # Set intersection
    if _is_set(a) and _is_set(b):
        result = _get_set_value(a) & _get_set_value(b)
        if ctx.strict:
            ctx.stack.push_value(JoyValue.joy_set(result))
        else:
            ctx.stack.push(result)
    else:
        result = _is_truthy(a) and _is_truthy(b)
        _push_boolean(ctx, result)


@joy_word(name="or", params=2, doc="B1 B2 -> B | S1 S2 -> S")
def or_word(ctx: ExecutionContext) -> None:
    """Logical or, or set union."""
    b, a = ctx.stack.pop_n(2)
    # Set union
    if _is_set(a) and _is_set(b):
        result = _get_set_value(a) | _get_set_value(b)
        if ctx.strict:
            ctx.stack.push_value(JoyValue.joy_set(result))
        else:
            ctx.stack.push(result)
    else:
        result = _is_truthy(a) or _is_truthy(b)
        _push_boolean(ctx, result)


@joy_word(name="not", params=1, doc="B -> B | S -> S")
def not_word(ctx: ExecutionContext) -> None:
    """Logical not, or set complement."""
    a = ctx.stack.pop()
    # Set complement (all 64 possible members minus current)
    if _is_set(a):
        all_members = frozenset(range(64))
        result = all_members - _get_set_value(a)
        if ctx.strict:
            ctx.stack.push_value(JoyValue.joy_set(result))
        else:
            ctx.stack.push(result)
    else:
        result = not _is_truthy(a)
        _push_boolean(ctx, result)


@joy_word(name="xor", params=2, doc="B1 B2 -> B | S1 S2 -> S")
def xor_word(ctx: ExecutionContext) -> None:
    """Logical exclusive or, or set symmetric difference."""
    b, a = ctx.stack.pop_n(2)
    # Set symmetric difference
    if _is_set(a) and _is_set(b):
        result = _get_set_value(a) ^ _get_set_value(b)
        if ctx.strict:
            ctx.stack.push_value(JoyValue.joy_set(result))
        else:
            ctx.stack.push(result)
    else:
        result = _is_truthy(a) != _is_truthy(b)
        _push_boolean(ctx, result)


# -----------------------------------------------------------------------------
# Boolean Constants
# -----------------------------------------------------------------------------


@joy_word(name="true", params=0, doc="-> B")
def true_(ctx: ExecutionContext) -> None:
    """Push true."""
    if ctx.strict:
        ctx.stack.push_value(JoyValue.boolean(True))
    else:
        ctx.stack.push(True)


@joy_word(name="false", params=0, doc="-> B")
def false_(ctx: ExecutionContext) -> None:
    """Push false."""
    if ctx.strict:
        ctx.stack.push_value(JoyValue.boolean(False))
    else:
        ctx.stack.push(False)
