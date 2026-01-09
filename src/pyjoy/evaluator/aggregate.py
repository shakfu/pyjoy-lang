"""
pyjoy.evaluator.aggregate - List, string, and set operations.

Contains: cons, swons, first, rest, uncons, unswons, null, small, size,
concat, reverse, at, of, drop, take, in, has, enconcat, swoncat
"""

from __future__ import annotations

from typing import Any

from pyjoy.errors import JoyEmptyAggregate, JoyTypeError
from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyQuotation, JoyType, JoyValue

from .core import is_joy_value, joy_word


def _term_to_value(term) -> JoyValue:
    """Convert a quotation term to a JoyValue."""
    if isinstance(term, JoyValue):
        return term
    elif isinstance(term, str):
        # Symbol
        return JoyValue.symbol(term)
    elif isinstance(term, JoyQuotation):
        return JoyValue.quotation(term)
    elif isinstance(term, int):
        return JoyValue.integer(term)
    elif isinstance(term, float):
        return JoyValue.floating(term)
    elif isinstance(term, bool):
        return JoyValue.boolean(term)
    else:
        # Fallback - treat as symbol
        return JoyValue.symbol(str(term))


def _get_value_type(v: Any) -> str:
    """Get the type category of a value (works in both modes)."""
    if is_joy_value(v):
        return v.type.name
    if isinstance(v, bool):
        return "BOOLEAN"
    if isinstance(v, int):
        return "INTEGER"
    if isinstance(v, float):
        return "FLOAT"
    if isinstance(v, str):
        return "STRING"
    if isinstance(v, (list, tuple)):
        return "LIST"
    if isinstance(v, JoyQuotation):
        return "QUOTATION"
    if isinstance(v, frozenset):
        return "SET"
    return "OBJECT"


def _get_aggregate(v: Any, op: str) -> tuple:
    """Extract aggregate contents as tuple (raw terms for quotations).

    Mode-aware: handles both JoyValue and raw Python values.
    """
    if is_joy_value(v):
        if v.type == JoyType.LIST:
            return v.value
        elif v.type == JoyType.QUOTATION:
            return v.value.terms
        elif v.type == JoyType.STRING:
            return tuple(JoyValue.char(c) for c in v.value)
        elif v.type == JoyType.SET:
            return tuple(JoyValue.integer(x) for x in sorted(v.value))
        else:
            raise JoyTypeError(op, "aggregate", v.type.name)
    else:
        # Raw Python values (pythonic mode)
        if isinstance(v, str):
            return tuple(v)  # String as tuple of chars
        elif isinstance(v, (list, tuple)):
            return tuple(v)
        elif isinstance(v, JoyQuotation):
            return v.terms
        elif isinstance(v, frozenset):
            return tuple(sorted(v))
        else:
            raise JoyTypeError(op, "aggregate", type(v).__name__)


def _get_original_type(v: Any) -> JoyType | str:
    """Get the original type for reconstructing aggregates."""
    if is_joy_value(v):
        return v.type
    if isinstance(v, str):
        return "STRING"
    if isinstance(v, (list, tuple)):
        return "LIST"
    if isinstance(v, JoyQuotation):
        return "QUOTATION"
    if isinstance(v, frozenset):
        return "SET"
    return "LIST"


def _make_aggregate(
    items: tuple, original_type: JoyType | str, strict: bool = True
) -> Any:
    """Create aggregate from items, matching original type where possible.

    Mode-aware: returns JoyValue in strict mode, raw Python in pythonic mode.
    """
    if strict:
        # Strict mode - return JoyValue
        if original_type in (JoyType.STRING, "STRING"):
            try:
                if items and is_joy_value(items[0]):
                    chars = "".join(
                        v.value for v in items
                        if is_joy_value(v) and v.type == JoyType.CHAR
                    )
                else:
                    chars = "".join(str(c) for c in items)
                return JoyValue.string(chars)
            except (AttributeError, TypeError):
                return JoyValue.list(items)
        elif original_type in (JoyType.SET, "SET"):
            try:
                if items and is_joy_value(items[0]):
                    members = frozenset(
                        v.value for v in items
                        if is_joy_value(v) and v.type == JoyType.INTEGER
                    )
                else:
                    members = frozenset(items)
                return JoyValue.joy_set(members)
            except Exception:
                return JoyValue.list(items)
        elif original_type in (JoyType.QUOTATION, "QUOTATION"):
            return JoyValue.quotation(JoyQuotation(items))
        else:
            return JoyValue.list(items)
    else:
        # Pythonic mode - return raw Python values
        if original_type in (JoyType.STRING, "STRING"):
            try:
                if items and is_joy_value(items[0]):
                    return "".join(
                        v.value for v in items
                        if is_joy_value(v) and v.type == JoyType.CHAR
                    )
                else:
                    return "".join(str(c) for c in items)
            except (AttributeError, TypeError):
                return list(items)
        elif original_type in (JoyType.SET, "SET"):
            try:
                if items and is_joy_value(items[0]):
                    return frozenset(
                        v.value for v in items
                        if is_joy_value(v) and v.type == JoyType.INTEGER
                    )
                else:
                    return frozenset(items)
            except Exception:
                return list(items)
        elif original_type in (JoyType.QUOTATION, "QUOTATION"):
            return JoyQuotation(items)
        else:
            return list(items)


# -----------------------------------------------------------------------------
# Basic Aggregate Operations
# -----------------------------------------------------------------------------


def _push_result(ctx: ExecutionContext, value: Any) -> None:
    """Push a result value in a mode-appropriate way."""
    if ctx.strict:
        ctx.stack.push_value(value)
    else:
        ctx.stack.push(value)


@joy_word(name="cons", params=2, doc="X A -> A")
def cons(ctx: ExecutionContext) -> None:
    """Prepend X to aggregate A."""
    agg, x = ctx.stack.pop_n(2)
    items = _get_aggregate(agg, "cons")
    new_items = (x,) + items
    orig_type = _get_original_type(agg)
    _push_result(ctx, _make_aggregate(new_items, orig_type, ctx.strict))


@joy_word(name="swons", params=2, doc="A X -> A")
def swons(ctx: ExecutionContext) -> None:
    """Swap and cons: A X -> [X | A]."""
    x, agg = ctx.stack.pop_n(2)
    items = _get_aggregate(agg, "swons")
    new_items = (x,) + items
    orig_type = _get_original_type(agg)
    _push_result(ctx, _make_aggregate(new_items, orig_type, ctx.strict))


@joy_word(name="first", params=1, doc="A -> X")
def first(ctx: ExecutionContext) -> None:
    """Get first element of aggregate."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "first")
    if not items:
        raise JoyEmptyAggregate("first")
    item = items[0]
    # Convert raw quotation terms to JoyValue in strict mode
    if ctx.strict and is_joy_value(agg) and agg.type == JoyType.QUOTATION:
        item = _term_to_value(item)
    _push_result(ctx, item)


@joy_word(name="rest", params=1, doc="A -> A")
def rest(ctx: ExecutionContext) -> None:
    """Get aggregate without first element."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "rest")
    if not items:
        raise JoyEmptyAggregate("rest")
    new_items = items[1:]
    orig_type = _get_original_type(agg)
    _push_result(ctx, _make_aggregate(new_items, orig_type, ctx.strict))


@joy_word(name="uncons", params=1, doc="A -> X A")
def uncons(ctx: ExecutionContext) -> None:
    """Split aggregate into first and rest."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "uncons")
    if not items:
        raise JoyEmptyAggregate("uncons")
    item = items[0]
    # Convert raw quotation terms to JoyValue in strict mode
    if ctx.strict and is_joy_value(agg) and agg.type == JoyType.QUOTATION:
        item = _term_to_value(item)
    orig_type = _get_original_type(agg)
    _push_result(ctx, item)
    _push_result(ctx, _make_aggregate(items[1:], orig_type, ctx.strict))


@joy_word(name="unswons", params=1, doc="A -> A X")
def unswons(ctx: ExecutionContext) -> None:
    """Split aggregate into rest and first."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "unswons")
    if not items:
        raise JoyEmptyAggregate("unswons")
    item = items[0]
    # Convert raw quotation terms to JoyValue in strict mode
    if ctx.strict and is_joy_value(agg) and agg.type == JoyType.QUOTATION:
        item = _term_to_value(item)
    orig_type = _get_original_type(agg)
    _push_result(ctx, _make_aggregate(items[1:], orig_type, ctx.strict))
    _push_result(ctx, item)


# -----------------------------------------------------------------------------
# Aggregate Predicates
# -----------------------------------------------------------------------------


def _push_boolean(ctx: ExecutionContext, result: bool) -> None:
    """Push a boolean result in a mode-appropriate way."""
    if ctx.strict:
        ctx.stack.push_value(JoyValue.boolean(result))
    else:
        ctx.stack.push(result)


def _push_integer(ctx: ExecutionContext, result: int) -> None:
    """Push an integer result in a mode-appropriate way."""
    if ctx.strict:
        ctx.stack.push_value(JoyValue.integer(result))
    else:
        ctx.stack.push(result)


@joy_word(name="null", params=1, doc="X -> B")
def null(ctx: ExecutionContext) -> None:
    """Test if aggregate is empty or numeric is zero."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        if x.type in (JoyType.INTEGER, JoyType.FLOAT):
            result = x.value == 0
        elif x.type == JoyType.BOOLEAN:
            result = not x.value
        elif x.type == JoyType.CHAR:
            result = ord(x.value) == 0
        elif x.type in (JoyType.LIST, JoyType.QUOTATION, JoyType.STRING, JoyType.SET):
            items = _get_aggregate(x, "null")
            result = len(items) == 0
        elif x.type == JoyType.FILE:
            result = x.value is None
        else:
            result = False
    else:
        # Raw Python values (pythonic mode)
        if isinstance(x, bool):
            result = not x
        elif isinstance(x, (int, float)):
            result = x == 0
        elif isinstance(x, str):
            result = len(x) == 0
        elif isinstance(x, (list, tuple, JoyQuotation)):
            items = _get_aggregate(x, "null")
            result = len(items) == 0
        elif isinstance(x, frozenset):
            result = len(x) == 0
        elif x is None:
            result = True
        else:
            result = False
    _push_boolean(ctx, result)


@joy_word(name="small", params=1, doc="X -> B")
def small(ctx: ExecutionContext) -> None:
    """Test if aggregate has 0 or 1 elements, or numeric < 2."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        if x.type in (JoyType.INTEGER, JoyType.FLOAT):
            result = x.value < 2
        elif x.type == JoyType.BOOLEAN:
            result = True  # true and false are both "small"
        elif x.type == JoyType.CHAR:
            result = ord(x.value) < 2
        elif x.type in (JoyType.LIST, JoyType.QUOTATION, JoyType.STRING, JoyType.SET):
            items = _get_aggregate(x, "small")
            result = len(items) <= 1
        else:
            result = False
    else:
        # Raw Python values (pythonic mode)
        if isinstance(x, bool):
            result = True  # true and false are both "small"
        elif isinstance(x, (int, float)):
            result = x < 2
        elif isinstance(x, str):
            result = len(x) <= 1
        elif isinstance(x, (list, tuple, JoyQuotation)):
            items = _get_aggregate(x, "small")
            result = len(items) <= 1
        elif isinstance(x, frozenset):
            result = len(x) <= 1
        else:
            result = False
    _push_boolean(ctx, result)


@joy_word(name="size", params=1, doc="A -> N")
def size(ctx: ExecutionContext) -> None:
    """Get size of aggregate."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "size")
    _push_integer(ctx, len(items))


# -----------------------------------------------------------------------------
# Aggregate Manipulation
# -----------------------------------------------------------------------------


@joy_word(name="concat", params=2, doc="A1 A2 -> A")
def concat(ctx: ExecutionContext) -> None:
    """Concatenate two aggregates."""
    b, a = ctx.stack.pop_n(2)
    items_a = _get_aggregate(a, "concat")
    items_b = _get_aggregate(b, "concat")
    new_items = items_a + items_b
    orig_type = _get_original_type(a)
    _push_result(ctx, _make_aggregate(new_items, orig_type, ctx.strict))


@joy_word(name="swoncat", params=2, doc="A1 A2 -> A")
def swoncat(ctx: ExecutionContext) -> None:
    """Swap and concatenate: A1 A2 -> (A2 ++ A1)."""
    a2, a1 = ctx.stack.pop_n(2)  # a2 is TOS, a1 is below
    items_a2 = _get_aggregate(a2, "swoncat")
    items_a1 = _get_aggregate(a1, "swoncat")
    # swoncat = swap concat, so result is A2 ++ A1
    new_items = items_a2 + items_a1
    orig_type = _get_original_type(a2)
    _push_result(ctx, _make_aggregate(new_items, orig_type, ctx.strict))


@joy_word(name="enconcat", params=3, doc="X A1 A2 -> A")
def enconcat(ctx: ExecutionContext) -> None:
    """Concatenate A1, [X], A2."""
    a2, a1, x = ctx.stack.pop_n(3)
    items1 = _get_aggregate(a1, "enconcat")
    items2 = _get_aggregate(a2, "enconcat")
    new_items = items1 + (x,) + items2
    orig_type = _get_original_type(a1)
    _push_result(ctx, _make_aggregate(new_items, orig_type, ctx.strict))


@joy_word(name="reverse", params=1, doc="A -> A")
def reverse(ctx: ExecutionContext) -> None:
    """Reverse an aggregate."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "reverse")
    new_items = items[::-1]
    orig_type = _get_original_type(agg)
    _push_result(ctx, _make_aggregate(new_items, orig_type, ctx.strict))


# -----------------------------------------------------------------------------
# Indexing
# -----------------------------------------------------------------------------


def _get_int_value(v: Any, op: str) -> int:
    """Extract integer value from JoyValue or raw int."""
    if is_joy_value(v):
        if v.type != JoyType.INTEGER:
            raise JoyTypeError(op, "INTEGER", v.type.name)
        return v.value
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    raise JoyTypeError(op, "INTEGER", type(v).__name__)


@joy_word(name="at", params=2, doc="A N -> X")
def at(ctx: ExecutionContext) -> None:
    """Get element at index N from aggregate A."""
    n, agg = ctx.stack.pop_n(2)
    idx = _get_int_value(n, "at")
    items = _get_aggregate(agg, "at")
    if idx < 0 or idx >= len(items):
        raise JoyEmptyAggregate(f"at: index {idx} out of bounds")
    item = items[idx]
    # Convert raw quotation terms to JoyValue in strict mode
    if ctx.strict and is_joy_value(agg) and agg.type == JoyType.QUOTATION:
        item = _term_to_value(item)
    _push_result(ctx, item)


@joy_word(name="of", params=2, doc="N A -> X")
def of(ctx: ExecutionContext) -> None:
    """Get element at index N from aggregate A (N A -> X, reverse of at)."""
    agg, n = ctx.stack.pop_n(2)
    idx = _get_int_value(n, "of")
    items = _get_aggregate(agg, "of")
    if idx < 0 or idx >= len(items):
        raise JoyEmptyAggregate(f"of: index {idx} out of bounds")
    item = items[idx]
    # Convert raw quotation terms to JoyValue in strict mode
    if ctx.strict and is_joy_value(agg) and agg.type == JoyType.QUOTATION:
        item = _term_to_value(item)
    _push_result(ctx, item)


@joy_word(name="pick", params=1, doc="X0 X1 ... Xn N -> X0 X1 ... Xn Xn-N")
def pick(ctx: ExecutionContext) -> None:
    """Pick element at index N from stack (0=dup, 1=over)."""
    n = ctx.stack.pop()
    idx = _get_int_value(n, "pick")
    # Get stack items (don't pop them)
    stack_items = ctx.stack._items
    if idx >= len(stack_items):
        # If index too large, pick the bottom element
        idx = len(stack_items) - 1
    if idx < 0:
        idx = 0
    if not stack_items:
        raise JoyEmptyAggregate("pick: stack is empty")
    # Pick from top: 0 = TOS, 1 = second from top, etc.
    item = stack_items[-(idx + 1)]
    _push_result(ctx, item)


# -----------------------------------------------------------------------------
# Take and Drop
# -----------------------------------------------------------------------------


@joy_word(name="drop", params=2, doc="A N -> A'")
def drop_(ctx: ExecutionContext) -> None:
    """Drop first N elements from aggregate."""
    n = ctx.stack.pop()
    a = ctx.stack.pop()
    count = _get_int_value(n, "drop")
    orig_type = _get_original_type(a)

    if is_joy_value(a):
        if a.type == JoyType.LIST:
            result = a.value[count:] if count < len(a.value) else ()
            _push_result(ctx, _make_aggregate(result, orig_type, ctx.strict))
        elif a.type == JoyType.QUOTATION:
            terms = a.value.terms
            result = terms[count:] if count < len(terms) else ()
            _push_result(ctx, _make_aggregate(result, orig_type, ctx.strict))
        elif a.type == JoyType.STRING:
            result = a.value[count:] if count < len(a.value) else ""
            _push_result(ctx, _make_aggregate(tuple(result), orig_type, ctx.strict))
        elif a.type == JoyType.SET:
            sorted_items = sorted(a.value)
            result = sorted_items[count:] if count < len(sorted_items) else []
            _push_result(ctx, _make_aggregate(tuple(result), orig_type, ctx.strict))
        else:
            raise JoyTypeError("drop", "aggregate", a.type.name)
    else:
        # Raw Python values (pythonic mode)
        if isinstance(a, str):
            result = a[count:] if count < len(a) else ""
            _push_result(ctx, result)
        elif isinstance(a, (list, tuple)):
            result = list(a)[count:] if count < len(a) else []
            _push_result(ctx, result)
        elif isinstance(a, frozenset):
            sorted_items = sorted(a)
            if count < len(sorted_items):
                result = frozenset(sorted_items[count:])
            else:
                result = frozenset()
            _push_result(ctx, result)
        elif isinstance(a, JoyQuotation):
            terms = a.terms
            result = terms[count:] if count < len(terms) else ()
            _push_result(ctx, JoyQuotation(result))
        else:
            raise JoyTypeError("drop", "aggregate", type(a).__name__)


@joy_word(name="take", params=2, doc="A N -> A'")
def take_(ctx: ExecutionContext) -> None:
    """Take first N elements from aggregate."""
    n = ctx.stack.pop()
    a = ctx.stack.pop()
    count = _get_int_value(n, "take")
    orig_type = _get_original_type(a)

    if is_joy_value(a):
        if a.type == JoyType.LIST:
            result = a.value[:count]
            _push_result(ctx, _make_aggregate(result, orig_type, ctx.strict))
        elif a.type == JoyType.QUOTATION:
            terms = a.value.terms
            result = terms[:count]
            _push_result(ctx, _make_aggregate(result, orig_type, ctx.strict))
        elif a.type == JoyType.STRING:
            result = a.value[:count]
            _push_result(ctx, _make_aggregate(tuple(result), orig_type, ctx.strict))
        elif a.type == JoyType.SET:
            sorted_items = sorted(a.value)
            result = sorted_items[:count]
            _push_result(ctx, _make_aggregate(tuple(result), orig_type, ctx.strict))
        else:
            raise JoyTypeError("take", "aggregate", a.type.name)
    else:
        # Raw Python values (pythonic mode)
        if isinstance(a, str):
            result = a[:count]
            _push_result(ctx, result)
        elif isinstance(a, (list, tuple)):
            result = list(a)[:count]
            _push_result(ctx, result)
        elif isinstance(a, frozenset):
            sorted_items = sorted(a)
            result = frozenset(sorted_items[:count])
            _push_result(ctx, result)
        elif isinstance(a, JoyQuotation):
            terms = a.terms
            result = terms[:count]
            _push_result(ctx, JoyQuotation(result))
        else:
            raise JoyTypeError("take", "aggregate", type(a).__name__)


# -----------------------------------------------------------------------------
# Membership
# -----------------------------------------------------------------------------


def _get_raw_value(v: Any) -> Any:
    """Get the raw Python value from a JoyValue or return as-is."""
    if is_joy_value(v):
        return v.value
    return v


def _item_equals(x: Any, item: Any) -> bool:
    """Check if two items are equal (mode-aware)."""
    if is_joy_value(x) and is_joy_value(item):
        if x.type == item.type:
            return x.value == item.value
        # Allow int/float comparison
        if x.is_numeric() and item.is_numeric():
            return x.value == item.value
        return False
    else:
        # Raw Python values or mixed
        xv = _get_raw_value(x)
        iv = _get_raw_value(item)
        return xv == iv


@joy_word(name="in", params=2, doc="X A -> B")
def in_(ctx: ExecutionContext) -> None:
    """Test if X is a member of aggregate A."""
    agg, x = ctx.stack.pop_n(2)

    if is_joy_value(agg):
        if agg.type == JoyType.SET:
            xv = _get_raw_value(x)
            if isinstance(xv, int) and not isinstance(xv, bool):
                result = xv in agg.value
            else:
                result = False
        elif agg.type in (JoyType.LIST, JoyType.QUOTATION, JoyType.STRING):
            items = _get_aggregate(agg, "in")
            result = any(_item_equals(x, item) for item in items)
        else:
            raise JoyTypeError("in", "aggregate", agg.type.name)
    else:
        # Raw Python values (pythonic mode)
        if isinstance(agg, frozenset):
            xv = _get_raw_value(x)
            result = xv in agg
        elif isinstance(agg, str):
            xv = _get_raw_value(x)
            result = xv in agg
        elif isinstance(agg, (list, tuple)):
            xv = _get_raw_value(x)
            result = xv in agg
        elif isinstance(agg, JoyQuotation):
            items = _get_aggregate(agg, "in")
            result = any(_item_equals(x, item) for item in items)
        else:
            raise JoyTypeError("in", "aggregate", type(agg).__name__)

    _push_boolean(ctx, result)


@joy_word(name="has", params=2, doc="A X -> B")
def has_(ctx: ExecutionContext) -> None:
    """Test if aggregate A contains X (reverse of in)."""
    x, agg = ctx.stack.pop_n(2)

    if is_joy_value(agg):
        if agg.type == JoyType.SET:
            xv = _get_raw_value(x)
            if isinstance(xv, int) and not isinstance(xv, bool):
                result = xv in agg.value
            else:
                result = False
        elif agg.type in (JoyType.LIST, JoyType.QUOTATION, JoyType.STRING):
            items = _get_aggregate(agg, "has")
            result = any(_item_equals(x, item) for item in items)
        else:
            raise JoyTypeError("has", "aggregate", agg.type.name)
    else:
        # Raw Python values (pythonic mode)
        if isinstance(agg, frozenset):
            xv = _get_raw_value(x)
            result = xv in agg
        elif isinstance(agg, str):
            xv = _get_raw_value(x)
            result = xv in agg
        elif isinstance(agg, (list, tuple)):
            xv = _get_raw_value(x)
            result = xv in agg
        elif isinstance(agg, JoyQuotation):
            items = _get_aggregate(agg, "has")
            result = any(_item_equals(x, item) for item in items)
        else:
            raise JoyTypeError("has", "aggregate", type(agg).__name__)

    _push_boolean(ctx, result)
