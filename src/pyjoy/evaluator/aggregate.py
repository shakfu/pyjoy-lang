"""
pyjoy.evaluator.aggregate - List, string, and set operations.

Contains: cons, swons, first, rest, uncons, unswons, null, small, size,
concat, reverse, at, of, drop, take, in, has, enconcat, swoncat
"""

from __future__ import annotations

from pyjoy.errors import JoyEmptyAggregate, JoyTypeError
from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyQuotation, JoyType, JoyValue

from .core import joy_word


def _get_aggregate(v: JoyValue, op: str) -> tuple:
    """Extract aggregate contents as tuple."""
    if v.type == JoyType.LIST:
        return v.value
    elif v.type == JoyType.QUOTATION:
        return v.value.terms
    elif v.type == JoyType.STRING:
        # String as tuple of chars
        return tuple(JoyValue.char(c) for c in v.value)
    elif v.type == JoyType.SET:
        return tuple(JoyValue.integer(x) for x in sorted(v.value))
    else:
        raise JoyTypeError(op, "aggregate", v.type.name)


def _make_aggregate(items: tuple, original_type: JoyType) -> JoyValue:
    """Create aggregate from items, matching original type where possible."""
    if original_type == JoyType.STRING:
        # Try to convert back to string
        try:
            chars = "".join(v.value for v in items if v.type == JoyType.CHAR)
            return JoyValue.string(chars)
        except (AttributeError, TypeError):
            return JoyValue.list(items)
    elif original_type == JoyType.SET:
        # Convert back to set
        try:
            members = frozenset(v.value for v in items if v.type == JoyType.INTEGER)
            return JoyValue.joy_set(members)
        except Exception:
            return JoyValue.list(items)
    else:
        return JoyValue.list(items)


# -----------------------------------------------------------------------------
# Basic Aggregate Operations
# -----------------------------------------------------------------------------


@joy_word(name="cons", params=2, doc="X A -> A")
def cons(ctx: ExecutionContext) -> None:
    """Prepend X to aggregate A."""
    agg, x = ctx.stack.pop_n(2)
    items = _get_aggregate(agg, "cons")
    new_items = (x,) + items
    ctx.stack.push_value(_make_aggregate(new_items, agg.type))


@joy_word(name="swons", params=2, doc="A X -> A")
def swons(ctx: ExecutionContext) -> None:
    """Swap and cons: A X -> [X | A]."""
    x, agg = ctx.stack.pop_n(2)
    items = _get_aggregate(agg, "swons")
    new_items = (x,) + items
    ctx.stack.push_value(_make_aggregate(new_items, agg.type))


@joy_word(name="first", params=1, doc="A -> X")
def first(ctx: ExecutionContext) -> None:
    """Get first element of aggregate."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "first")
    if not items:
        raise JoyEmptyAggregate("first")
    ctx.stack.push_value(items[0])


@joy_word(name="rest", params=1, doc="A -> A")
def rest(ctx: ExecutionContext) -> None:
    """Get aggregate without first element."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "rest")
    if not items:
        raise JoyEmptyAggregate("rest")
    new_items = items[1:]
    ctx.stack.push_value(_make_aggregate(new_items, agg.type))


@joy_word(name="uncons", params=1, doc="A -> X A")
def uncons(ctx: ExecutionContext) -> None:
    """Split aggregate into first and rest."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "uncons")
    if not items:
        raise JoyEmptyAggregate("uncons")
    ctx.stack.push_value(items[0])
    ctx.stack.push_value(_make_aggregate(items[1:], agg.type))


@joy_word(name="unswons", params=1, doc="A -> A X")
def unswons(ctx: ExecutionContext) -> None:
    """Split aggregate into rest and first."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "unswons")
    if not items:
        raise JoyEmptyAggregate("unswons")
    ctx.stack.push_value(_make_aggregate(items[1:], agg.type))
    ctx.stack.push_value(items[0])


# -----------------------------------------------------------------------------
# Aggregate Predicates
# -----------------------------------------------------------------------------


@joy_word(name="null", params=1, doc="X -> B")
def null(ctx: ExecutionContext) -> None:
    """Test if aggregate is empty or numeric is zero."""
    x = ctx.stack.pop()
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
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="small", params=1, doc="X -> B")
def small(ctx: ExecutionContext) -> None:
    """Test if aggregate has 0 or 1 elements, or numeric < 2."""
    x = ctx.stack.pop()
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
    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="size", params=1, doc="A -> N")
def size(ctx: ExecutionContext) -> None:
    """Get size of aggregate."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "size")
    ctx.stack.push_value(JoyValue.integer(len(items)))


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
    ctx.stack.push_value(_make_aggregate(new_items, a.type))


@joy_word(name="swoncat", params=2, doc="A1 A2 -> A")
def swoncat(ctx: ExecutionContext) -> None:
    """Swap and concatenate: A1 A2 -> (A2 ++ A1)."""
    a2, a1 = ctx.stack.pop_n(2)  # a2 is TOS, a1 is below
    items_a2 = _get_aggregate(a2, "swoncat")
    items_a1 = _get_aggregate(a1, "swoncat")
    # swoncat = swap concat, so result is A2 ++ A1
    new_items = items_a2 + items_a1
    ctx.stack.push_value(_make_aggregate(new_items, a2.type))


@joy_word(name="enconcat", params=3, doc="X A1 A2 -> A")
def enconcat(ctx: ExecutionContext) -> None:
    """Concatenate A1, [X], A2."""
    a2, a1, x = ctx.stack.pop_n(3)
    items1 = _get_aggregate(a1, "enconcat")
    items2 = _get_aggregate(a2, "enconcat")
    new_items = items1 + (x,) + items2
    ctx.stack.push_value(_make_aggregate(new_items, a1.type))


@joy_word(name="reverse", params=1, doc="A -> A")
def reverse(ctx: ExecutionContext) -> None:
    """Reverse an aggregate."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "reverse")
    new_items = items[::-1]
    ctx.stack.push_value(_make_aggregate(new_items, agg.type))


# -----------------------------------------------------------------------------
# Indexing
# -----------------------------------------------------------------------------


@joy_word(name="at", params=2, doc="A N -> X")
def at(ctx: ExecutionContext) -> None:
    """Get element at index N from aggregate A."""
    n, agg = ctx.stack.pop_n(2)
    if n.type != JoyType.INTEGER:
        raise JoyTypeError("at", "INTEGER", n.type.name)
    items = _get_aggregate(agg, "at")
    idx = n.value
    if idx < 0 or idx >= len(items):
        raise JoyEmptyAggregate(f"at: index {idx} out of bounds")
    ctx.stack.push_value(items[idx])


@joy_word(name="of", params=2, doc="N A -> X")
def of(ctx: ExecutionContext) -> None:
    """Get element at index N from aggregate A (N A -> X, reverse of at)."""
    agg, n = ctx.stack.pop_n(2)
    if n.type != JoyType.INTEGER:
        raise JoyTypeError("of", "INTEGER", n.type.name)
    items = _get_aggregate(agg, "of")
    idx = n.value
    if idx < 0 or idx >= len(items):
        raise JoyEmptyAggregate(f"of: index {idx} out of bounds")
    ctx.stack.push_value(items[idx])


@joy_word(name="pick", params=2, doc="A I -> X")
def pick(ctx: ExecutionContext) -> None:
    """Pick element at index I from aggregate A (like at)."""
    n, agg = ctx.stack.pop_n(2)
    if n.type != JoyType.INTEGER:
        raise JoyTypeError("pick", "INTEGER", n.type.name)
    items = _get_aggregate(agg, "pick")
    idx = n.value
    if idx < 0 or idx >= len(items):
        raise JoyEmptyAggregate(f"pick: index {idx} out of bounds")
    ctx.stack.push_value(items[idx])


# -----------------------------------------------------------------------------
# Take and Drop
# -----------------------------------------------------------------------------


@joy_word(name="drop", params=2, doc="A N -> A'")
def drop_(ctx: ExecutionContext) -> None:
    """Drop first N elements from aggregate."""
    n = ctx.stack.pop()
    a = ctx.stack.pop()

    if n.type != JoyType.INTEGER:
        raise JoyTypeError("drop", "INTEGER", n.type.name)

    count = n.value

    if a.type == JoyType.LIST:
        result = a.value[count:] if count < len(a.value) else ()
        ctx.stack.push_value(JoyValue.list(result))
    elif a.type == JoyType.QUOTATION:
        terms = a.value.terms
        result = terms[count:] if count < len(terms) else ()
        ctx.stack.push_value(JoyValue.quotation(JoyQuotation(result)))
    elif a.type == JoyType.STRING:
        result = a.value[count:] if count < len(a.value) else ""
        ctx.stack.push_value(JoyValue.string(result))
    elif a.type == JoyType.SET:
        sorted_items = sorted(a.value)
        result = (
            frozenset(sorted_items[count:])
            if count < len(sorted_items)
            else frozenset()
        )
        ctx.stack.push_value(JoyValue.joy_set(result))
    else:
        raise JoyTypeError("drop", "aggregate", a.type.name)


@joy_word(name="take", params=2, doc="A N -> A'")
def take_(ctx: ExecutionContext) -> None:
    """Take first N elements from aggregate."""
    n = ctx.stack.pop()
    a = ctx.stack.pop()

    if n.type != JoyType.INTEGER:
        raise JoyTypeError("take", "INTEGER", n.type.name)

    count = n.value

    if a.type == JoyType.LIST:
        result = a.value[:count]
        ctx.stack.push_value(JoyValue.list(result))
    elif a.type == JoyType.QUOTATION:
        terms = a.value.terms
        result = terms[:count]
        ctx.stack.push_value(JoyValue.quotation(JoyQuotation(result)))
    elif a.type == JoyType.STRING:
        result = a.value[:count]
        ctx.stack.push_value(JoyValue.string(result))
    elif a.type == JoyType.SET:
        sorted_items = sorted(a.value)
        result = frozenset(sorted_items[:count])
        ctx.stack.push_value(JoyValue.joy_set(result))
    else:
        raise JoyTypeError("take", "aggregate", a.type.name)


# -----------------------------------------------------------------------------
# Membership
# -----------------------------------------------------------------------------


@joy_word(name="in", params=2, doc="X A -> B")
def in_(ctx: ExecutionContext) -> None:
    """Test if X is a member of aggregate A."""
    agg, x = ctx.stack.pop_n(2)

    if agg.type == JoyType.SET:
        if x.type == JoyType.INTEGER:
            result = x.value in agg.value
        else:
            result = False
    elif agg.type in (JoyType.LIST, JoyType.QUOTATION, JoyType.STRING):
        items = _get_aggregate(agg, "in")
        result = any(_item_equals(x, item) for item in items)
    else:
        raise JoyTypeError("in", "aggregate", agg.type.name)

    ctx.stack.push_value(JoyValue.boolean(result))


@joy_word(name="has", params=2, doc="A X -> B")
def has_(ctx: ExecutionContext) -> None:
    """Test if aggregate A contains X (reverse of in)."""
    x, agg = ctx.stack.pop_n(2)

    if agg.type == JoyType.SET:
        if x.type == JoyType.INTEGER:
            result = x.value in agg.value
        else:
            result = False
    elif agg.type in (JoyType.LIST, JoyType.QUOTATION, JoyType.STRING):
        items = _get_aggregate(agg, "has")
        result = any(_item_equals(x, item) for item in items)
    else:
        raise JoyTypeError("has", "aggregate", agg.type.name)

    ctx.stack.push_value(JoyValue.boolean(result))


def _item_equals(x: JoyValue, item: JoyValue) -> bool:
    """Check if two items are equal."""
    if x.type == item.type:
        return x.value == item.value
    # Allow int/float comparison
    if x.is_numeric() and item.is_numeric():
        return x.value == item.value
    return False
