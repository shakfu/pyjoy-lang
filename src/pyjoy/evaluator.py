"""
pyjoy.evaluator - Joy stack machine execution.

Executes Joy programs by iterating through terms and manipulating the stack.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, Optional

from pyjoy.errors import (
    JoyDivisionByZero,
    JoyEmptyAggregate,
    JoyStackUnderflow,
    JoyTypeError,
    JoyUndefinedWord,
)
from pyjoy.parser import Parser, parse
from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyQuotation, JoyType, JoyValue

# Type alias for Joy word implementations
WordFunc = Callable[[ExecutionContext], None]

# Global registry for primitive words
_primitives: Dict[str, WordFunc] = {}


def joy_word(
    name: Optional[str] = None,
    params: int = 0,
    doc: Optional[str] = None,
) -> Callable[[Callable[..., None]], WordFunc]:
    """
    Decorator to define a Joy word implemented in Python.

    Args:
        name: Joy word name (defaults to function name)
        params: Required stack parameters
        doc: Documentation string (Joy signature like "X Y -> Z")

    Example:
        @joy_word(name="+", params=2, doc="N1 N2 -> N3")
        def plus(ctx):
            b, a = ctx.stack.pop_n(2)
            result = a.value + b.value
            ctx.stack.push(result)
    """

    def decorator(func: Callable[..., None]) -> WordFunc:
        word_name = name or func.__name__

        @wraps(func)
        def wrapper(ctx: ExecutionContext) -> None:
            # Validate parameter count
            if ctx.stack.depth < params:
                raise JoyStackUnderflow(word_name, params, ctx.stack.depth)

            # Execute the primitive
            func(ctx)

        # Store metadata on the wrapper
        wrapper.joy_word = word_name  # type: ignore[attr-defined]
        wrapper.joy_params = params  # type: ignore[attr-defined]
        wrapper.joy_doc = doc or func.__doc__  # type: ignore[attr-defined]

        # Register in global primitives
        _primitives[word_name] = wrapper
        return wrapper

    return decorator


def get_primitive(name: str) -> Optional[WordFunc]:
    """Get a registered primitive by name."""
    return _primitives.get(name)


def register_primitive(name: str, func: WordFunc) -> None:
    """Register a primitive without using the decorator."""
    _primitives[name] = func


def list_primitives() -> list[str]:
    """List all registered primitive names."""
    return sorted(_primitives.keys())


class Evaluator:
    """
    Joy evaluator: executes programs on a stack.

    Manages:
    - Execution context (stack + saved states)
    - User-defined words
    - Program execution
    """

    def __init__(self) -> None:
        self.ctx = ExecutionContext()
        self.ctx.set_evaluator(self)
        self.definitions: Dict[str, JoyQuotation] = {}

    def execute(self, program: JoyQuotation) -> None:
        """
        Execute a Joy program (quotation).

        Args:
            program: JoyQuotation to execute
        """
        for term in program.terms:
            self._execute_term(term)

    def run(self, source: str) -> None:
        """
        Parse and execute Joy source code.

        Handles both definitions and executable code.
        Definitions are registered before program execution.

        Args:
            source: Joy source code string
        """
        parser = Parser()
        result = parser.parse_full(source)

        # Register all definitions
        for defn in result.definitions:
            self.define(defn.name, defn.body)

        # Execute the program
        self.execute(result.program)

    def _execute_term(self, term: Any) -> None:
        """
        Execute a single term.

        Args:
            term: Can be JoyValue, JoyQuotation, or string (symbol)
        """
        if isinstance(term, JoyValue):
            # Literal value: push to stack
            self.ctx.stack.push_value(term)

        elif isinstance(term, JoyQuotation):
            # Quotation: wrap and push (don't execute)
            self.ctx.stack.push_value(JoyValue.quotation(term))

        elif isinstance(term, str):
            # Symbol: look up and execute
            self._execute_symbol(term)

        else:
            # Unknown: try to convert and push
            self.ctx.stack.push(term)

    def _execute_symbol(self, name: str) -> None:
        """
        Look up and execute a symbol.

        Args:
            name: Symbol name

        Raises:
            JoyUndefinedWord: If symbol is not defined
        """
        # Check primitives first
        primitive = get_primitive(name)
        if primitive is not None:
            primitive(self.ctx)
            return

        # Check user definitions
        if name in self.definitions:
            self.execute(self.definitions[name])
            return

        raise JoyUndefinedWord(name)

    def define(self, name: str, body: JoyQuotation) -> None:
        """
        Define a new word.

        Args:
            name: Word name
            body: Word body as a quotation
        """
        self.definitions[name] = body

    def execute_quotation(self, quot: JoyValue) -> None:
        """
        Execute a quotation value from the stack.

        Used by combinators like 'i'.

        Args:
            quot: JoyValue of type QUOTATION

        Raises:
            JoyTypeError: If quot is not a quotation
        """
        if quot.type != JoyType.QUOTATION:
            raise JoyTypeError("execute_quotation", "QUOTATION", quot.type.name)
        self.execute(quot.value)

    @property
    def stack(self):
        """Convenience access to the stack."""
        return self.ctx.stack


# ============================================================================
# Basic Primitives (Phase 1 - minimal set for testing)
# ============================================================================

# Stack Operations


@joy_word(name="dup", params=1, doc="X -> X X")
def dup(ctx: ExecutionContext) -> None:
    """Duplicate top of stack."""
    top = ctx.stack.peek()
    ctx.stack.push_value(top)


@joy_word(name="pop", params=1, doc="X ->")
def pop(ctx: ExecutionContext) -> None:
    """Remove top of stack."""
    ctx.stack.pop()


@joy_word(name="swap", params=2, doc="X Y -> Y X")
def swap(ctx: ExecutionContext) -> None:
    """Exchange top two stack items."""
    b, a = ctx.stack.pop_n(2)
    ctx.stack.push_value(b)
    ctx.stack.push_value(a)


@joy_word(name="stack", params=0, doc=".. -> .. [..]")
def stack_word(ctx: ExecutionContext) -> None:
    """Push a list of the current stack contents."""
    items = tuple(ctx.stack.items())
    ctx.stack.push_value(JoyValue.list(items))


@joy_word(name="unstack", params=1, doc="[X Y ..] -> X Y ..")
def unstack(ctx: ExecutionContext) -> None:
    """Replace stack with contents of list/quotation on top."""
    lst = ctx.stack.pop()
    if lst.type == JoyType.LIST:
        items = lst.value
    elif lst.type == JoyType.QUOTATION:
        # Quotation terms can be executed as a list
        items = lst.value.terms
    else:
        raise JoyTypeError("unstack", "LIST or QUOTATION", lst.type.name)
    ctx.stack.clear()
    for item in items:
        if isinstance(item, JoyValue):
            ctx.stack.push_value(item)
        else:
            # Symbol or other term - push as-is
            ctx.stack.push(item)


# Quotation execution


@joy_word(name="i", params=1, doc="[P] -> ...")
def i_combinator(ctx: ExecutionContext) -> None:
    """Execute quotation."""
    quot = ctx.stack.pop()
    if quot.type != JoyType.QUOTATION:
        raise JoyTypeError("i", "QUOTATION", quot.type.name)
    ctx.evaluator.execute(quot.value)


# I/O (minimal for Phase 1)


@joy_word(name=".", params=1, doc="X ->")
def print_top(ctx: ExecutionContext) -> None:
    """Pop and print top of stack."""
    top = ctx.stack.pop()
    print(repr(top))


@joy_word(name="newline", params=0, doc="->")
def newline(ctx: ExecutionContext) -> None:
    """Print a newline."""
    print()


# ============================================================================
# Phase 2: Basic Primitives
# ============================================================================

# ----------------------------------------------------------------------------
# Additional Stack Operations
# ----------------------------------------------------------------------------


@joy_word(name="over", params=2, doc="X Y -> X Y X")
def over(ctx: ExecutionContext) -> None:
    """Copy second item to top."""
    second = ctx.stack.peek(1)
    ctx.stack.push_value(second)


@joy_word(name="rotate", params=3, doc="X Y Z -> Y Z X")
def rotate(ctx: ExecutionContext) -> None:
    """Rotate top three items: X Y Z -> Y Z X."""
    z, y, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(y)
    ctx.stack.push_value(z)
    ctx.stack.push_value(x)


@joy_word(name="rollup", params=3, doc="X Y Z -> Z X Y")
def rollup(ctx: ExecutionContext) -> None:
    """Roll up top three items: X Y Z -> Z X Y."""
    z, y, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(z)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)


@joy_word(name="rolldown", params=3, doc="X Y Z -> Y Z X")
def rolldown(ctx: ExecutionContext) -> None:
    """Roll down top three items (same as rotate)."""
    z, y, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(y)
    ctx.stack.push_value(z)
    ctx.stack.push_value(x)


@joy_word(name="dupd", params=2, doc="X Y -> X X Y")
def dupd(ctx: ExecutionContext) -> None:
    """Duplicate second item."""
    y, x = ctx.stack.pop_n(2)
    ctx.stack.push_value(x)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)


@joy_word(name="popd", params=2, doc="X Y -> Y")
def popd(ctx: ExecutionContext) -> None:
    """Pop second item."""
    y, _ = ctx.stack.pop_n(2)
    ctx.stack.push_value(y)


@joy_word(name="swapd", params=3, doc="X Y Z -> Y X Z")
def swapd(ctx: ExecutionContext) -> None:
    """Swap second and third items."""
    z, y, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(y)
    ctx.stack.push_value(x)
    ctx.stack.push_value(z)


@joy_word(name="choice", params=3, doc="B T F -> X")
def choice(ctx: ExecutionContext) -> None:
    """If B is true, push T, else push F."""
    f, t, b = ctx.stack.pop_n(3)
    if b.is_truthy():
        ctx.stack.push_value(t)
    else:
        ctx.stack.push_value(f)


# ----------------------------------------------------------------------------
# Arithmetic Operations
# ----------------------------------------------------------------------------


def _numeric_value(v: JoyValue) -> int | float:
    """Extract numeric value, converting if needed."""
    if v.type == JoyType.INTEGER:
        return v.value
    elif v.type == JoyType.FLOAT:
        return v.value
    elif v.type == JoyType.CHAR:
        return ord(v.value)
    elif v.type == JoyType.BOOLEAN:
        return 1 if v.value else 0
    else:
        raise JoyTypeError("arithmetic", "numeric", v.type.name)


def _make_numeric(value: int | float) -> JoyValue:
    """Create JoyValue from numeric result, preserving int when possible."""
    if isinstance(value, float) and value.is_integer():
        return JoyValue.integer(int(value))
    elif isinstance(value, float):
        return JoyValue.floating(value)
    else:
        return JoyValue.integer(value)


@joy_word(name="+", params=2, doc="N1 N2 -> N3")
def add(ctx: ExecutionContext) -> None:
    """Add two numbers."""
    b, a = ctx.stack.pop_n(2)
    result = _numeric_value(a) + _numeric_value(b)
    ctx.stack.push_value(_make_numeric(result))


@joy_word(name="-", params=2, doc="N1 N2 -> N3")
def sub(ctx: ExecutionContext) -> None:
    """Subtract: N1 - N2."""
    b, a = ctx.stack.pop_n(2)
    result = _numeric_value(a) - _numeric_value(b)
    ctx.stack.push_value(_make_numeric(result))


@joy_word(name="*", params=2, doc="N1 N2 -> N3")
def mul(ctx: ExecutionContext) -> None:
    """Multiply two numbers."""
    b, a = ctx.stack.pop_n(2)
    result = _numeric_value(a) * _numeric_value(b)
    ctx.stack.push_value(_make_numeric(result))


@joy_word(name="/", params=2, doc="N1 N2 -> N3")
def div(ctx: ExecutionContext) -> None:
    """Divide: N1 / N2. Integer division for integers."""
    b, a = ctx.stack.pop_n(2)
    bv = _numeric_value(b)
    if bv == 0:
        raise JoyDivisionByZero("/")
    av = _numeric_value(a)
    # Integer division if both are integers
    if isinstance(av, int) and isinstance(bv, int):
        result = av // bv
    else:
        result = av / bv
    ctx.stack.push_value(_make_numeric(result))


@joy_word(name="rem", params=2, doc="N1 N2 -> N3")
def rem(ctx: ExecutionContext) -> None:
    """Remainder: N1 % N2."""
    b, a = ctx.stack.pop_n(2)
    bv = _numeric_value(b)
    if bv == 0:
        raise JoyDivisionByZero("rem")
    result = _numeric_value(a) % bv
    ctx.stack.push_value(_make_numeric(result))


@joy_word(name="div", params=2, doc="N1 N2 -> Q R")
def divmod_word(ctx: ExecutionContext) -> None:
    """Integer division with remainder: push quotient then remainder."""
    b, a = ctx.stack.pop_n(2)
    bv = _numeric_value(b)
    if bv == 0:
        raise JoyDivisionByZero("div")
    av = _numeric_value(a)
    q = int(av // bv)
    r = av % bv
    ctx.stack.push_value(_make_numeric(q))
    ctx.stack.push_value(_make_numeric(r))


@joy_word(name="abs", params=1, doc="N -> N")
def abs_word(ctx: ExecutionContext) -> None:
    """Absolute value."""
    a = ctx.stack.pop()
    result = abs(_numeric_value(a))
    ctx.stack.push_value(_make_numeric(result))


@joy_word(name="neg", params=1, doc="N -> N")
def neg(ctx: ExecutionContext) -> None:
    """Negate: -N."""
    a = ctx.stack.pop()
    result = -_numeric_value(a)
    ctx.stack.push_value(_make_numeric(result))


@joy_word(name="sign", params=1, doc="N -> I")
def sign(ctx: ExecutionContext) -> None:
    """Sign: -1, 0, or 1."""
    a = ctx.stack.pop()
    v = _numeric_value(a)
    if v < 0:
        result = -1
    elif v > 0:
        result = 1
    else:
        result = 0
    ctx.stack.push_value(JoyValue.integer(result))


@joy_word(name="succ", params=1, doc="N -> N")
def succ(ctx: ExecutionContext) -> None:
    """Successor: N + 1."""
    a = ctx.stack.pop()
    result = _numeric_value(a) + 1
    ctx.stack.push_value(_make_numeric(result))


@joy_word(name="pred", params=1, doc="N -> N")
def pred(ctx: ExecutionContext) -> None:
    """Predecessor: N - 1."""
    a = ctx.stack.pop()
    result = _numeric_value(a) - 1
    ctx.stack.push_value(_make_numeric(result))


@joy_word(name="max", params=2, doc="N1 N2 -> N")
def max_word(ctx: ExecutionContext) -> None:
    """Maximum of two numbers."""
    b, a = ctx.stack.pop_n(2)
    av, bv = _numeric_value(a), _numeric_value(b)
    result = av if av >= bv else bv
    ctx.stack.push_value(_make_numeric(result))


@joy_word(name="min", params=2, doc="N1 N2 -> N")
def min_word(ctx: ExecutionContext) -> None:
    """Minimum of two numbers."""
    b, a = ctx.stack.pop_n(2)
    av, bv = _numeric_value(a), _numeric_value(b)
    result = av if av <= bv else bv
    ctx.stack.push_value(_make_numeric(result))


# ----------------------------------------------------------------------------
# Comparison Operations
# ----------------------------------------------------------------------------


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


# ----------------------------------------------------------------------------
# Boolean Operations
# ----------------------------------------------------------------------------


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


# ----------------------------------------------------------------------------
# List/Aggregate Operations
# ----------------------------------------------------------------------------


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


@joy_word(name="concat", params=2, doc="A1 A2 -> A")
def concat(ctx: ExecutionContext) -> None:
    """Concatenate two aggregates."""
    b, a = ctx.stack.pop_n(2)
    items_a = _get_aggregate(a, "concat")
    items_b = _get_aggregate(b, "concat")
    new_items = items_a + items_b
    ctx.stack.push_value(_make_aggregate(new_items, a.type))


@joy_word(name="reverse", params=1, doc="A -> A")
def reverse(ctx: ExecutionContext) -> None:
    """Reverse an aggregate."""
    agg = ctx.stack.pop()
    items = _get_aggregate(agg, "reverse")
    new_items = items[::-1]
    ctx.stack.push_value(_make_aggregate(new_items, agg.type))


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


# ----------------------------------------------------------------------------
# Type Predicates
# ----------------------------------------------------------------------------


@joy_word(name="integer", params=1, doc="X -> B")
def is_integer(ctx: ExecutionContext) -> None:
    """Test if X is an integer."""
    x = ctx.stack.pop()
    ctx.stack.push_value(JoyValue.boolean(x.type == JoyType.INTEGER))


@joy_word(name="float", params=1, doc="X -> B")
def is_float(ctx: ExecutionContext) -> None:
    """Test if X is a float."""
    x = ctx.stack.pop()
    ctx.stack.push_value(JoyValue.boolean(x.type == JoyType.FLOAT))


@joy_word(name="char", params=1, doc="X -> B")
def is_char(ctx: ExecutionContext) -> None:
    """Test if X is a character."""
    x = ctx.stack.pop()
    ctx.stack.push_value(JoyValue.boolean(x.type == JoyType.CHAR))


@joy_word(name="string", params=1, doc="X -> B")
def is_string(ctx: ExecutionContext) -> None:
    """Test if X is a string."""
    x = ctx.stack.pop()
    ctx.stack.push_value(JoyValue.boolean(x.type == JoyType.STRING))


@joy_word(name="list", params=1, doc="X -> B")
def is_list(ctx: ExecutionContext) -> None:
    """Test if X is a list."""
    x = ctx.stack.pop()
    ctx.stack.push_value(JoyValue.boolean(x.type == JoyType.LIST))


@joy_word(name="logical", params=1, doc="X -> B")
def is_logical(ctx: ExecutionContext) -> None:
    """Test if X is a boolean."""
    x = ctx.stack.pop()
    ctx.stack.push_value(JoyValue.boolean(x.type == JoyType.BOOLEAN))


# ============================================================================
# Phase 3: Higher-Order Operations (Combinators)
# ============================================================================

# ----------------------------------------------------------------------------
# Execution Combinators
# ----------------------------------------------------------------------------


def _expect_quotation(v: JoyValue, op: str) -> JoyQuotation:
    """Extract quotation, raising error if not a quotation."""
    if v.type != JoyType.QUOTATION:
        raise JoyTypeError(op, "QUOTATION", v.type.name)
    return v.value


@joy_word(name="x", params=1, doc="[P] -> ... [P]")
def x_combinator(ctx: ExecutionContext) -> None:
    """Execute quotation without consuming it."""
    quot = ctx.stack.peek()
    q = _expect_quotation(quot, "x")
    ctx.evaluator.execute(q)


@joy_word(name="dip", params=2, doc="X [P] -> ... X")
def dip(ctx: ExecutionContext) -> None:
    """Execute P with X temporarily removed, then restore X."""
    quot, x = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "dip")
    ctx.evaluator.execute(q)
    ctx.stack.push_value(x)


@joy_word(name="dipd", params=3, doc="X Y [P] -> ... X Y")
def dipd(ctx: ExecutionContext) -> None:
    """Execute P with X and Y temporarily removed."""
    quot, y, x = ctx.stack.pop_n(3)
    q = _expect_quotation(quot, "dipd")
    ctx.evaluator.execute(q)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)


@joy_word(name="dipdd", params=4, doc="X Y Z [P] -> ... X Y Z")
def dipdd(ctx: ExecutionContext) -> None:
    """Execute P with X, Y, Z temporarily removed."""
    quot, z, y, x = ctx.stack.pop_n(4)
    q = _expect_quotation(quot, "dipdd")
    ctx.evaluator.execute(q)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)
    ctx.stack.push_value(z)


@joy_word(name="keep", params=2, doc="X [P] -> ... X")
def keep(ctx: ExecutionContext) -> None:
    """Execute P on X, then restore X."""
    quot, x = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "keep")
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)
    ctx.stack.push_value(x)


@joy_word(name="nullary", params=1, doc="[P] -> X")
def nullary(ctx: ExecutionContext) -> None:
    """Execute P, save result, restore original stack, push result."""
    quot = ctx.stack.pop()
    q = _expect_quotation(quot, "nullary")
    saved = ctx.stack._items.copy()
    ctx.evaluator.execute(q)
    result = ctx.stack.pop()
    ctx.stack._items = saved
    ctx.stack.push_value(result)


@joy_word(name="unary", params=2, doc="X [P] -> R")
def unary(ctx: ExecutionContext) -> None:
    """Execute P on X, save result, restore stack below X, push result."""
    quot, x = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "unary")
    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)
    result = ctx.stack.pop()
    ctx.stack._items = saved
    ctx.stack.push_value(result)


@joy_word(name="binary", params=3, doc="X Y [P] -> R")
def binary(ctx: ExecutionContext) -> None:
    """Execute P on X and Y, save result, restore stack, push result."""
    quot, y, x = ctx.stack.pop_n(3)
    q = _expect_quotation(quot, "binary")
    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)
    ctx.evaluator.execute(q)
    result = ctx.stack.pop()
    ctx.stack._items = saved
    ctx.stack.push_value(result)


@joy_word(name="ternary", params=4, doc="X Y Z [P] -> R")
def ternary(ctx: ExecutionContext) -> None:
    """Execute P on X, Y, Z, save result, restore stack, push result."""
    quot, z, y, x = ctx.stack.pop_n(4)
    q = _expect_quotation(quot, "ternary")
    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)
    ctx.stack.push_value(z)
    ctx.evaluator.execute(q)
    result = ctx.stack.pop()
    ctx.stack._items = saved
    ctx.stack.push_value(result)


# ----------------------------------------------------------------------------
# Conditional Combinators
# ----------------------------------------------------------------------------


@joy_word(name="ifte", params=3, doc="[B] [T] [F] -> ...")
def ifte(ctx: ExecutionContext) -> None:
    """If-then-else: execute B, if true execute T, else execute F."""
    f_quot, t_quot, b_quot = ctx.stack.pop_n(3)
    b = _expect_quotation(b_quot, "ifte")
    t = _expect_quotation(t_quot, "ifte")
    f = _expect_quotation(f_quot, "ifte")

    # Save stack state
    saved = ctx.stack._items.copy()

    # Execute condition
    ctx.evaluator.execute(b)
    test_result = ctx.stack.pop()

    # Restore stack
    ctx.stack._items = saved

    # Execute appropriate branch
    if test_result.is_truthy():
        ctx.evaluator.execute(t)
    else:
        ctx.evaluator.execute(f)


@joy_word(name="branch", params=3, doc="B [T] [F] -> ...")
def branch(ctx: ExecutionContext) -> None:
    """If B is true execute T, else execute F."""
    f_quot, t_quot, b = ctx.stack.pop_n(3)
    t = _expect_quotation(t_quot, "branch")
    f = _expect_quotation(f_quot, "branch")

    if b.is_truthy():
        ctx.evaluator.execute(t)
    else:
        ctx.evaluator.execute(f)


@joy_word(name="cond", params=1, doc="[[B1 T1] [B2 T2] ... [Bn Tn] [D]] -> ...")
def cond(ctx: ExecutionContext) -> None:
    """Multi-way conditional. Each clause is [condition body]."""
    clauses = ctx.stack.pop()
    clause_list = _get_aggregate(clauses, "cond")

    if not clause_list:
        return  # Empty cond does nothing

    # Save stack for condition testing
    saved = ctx.stack._items.copy()

    for clause in clause_list:
        if not isinstance(clause, JoyValue) or clause.type != JoyType.QUOTATION:
            raise JoyTypeError("cond", "QUOTATION clause", type(clause).__name__)

        clause_terms = clause.value.terms
        if len(clause_terms) < 1:
            continue

        # Last clause might be default (single element)
        if len(clause_terms) == 1:
            # Default clause - just execute it
            ctx.stack._items = saved.copy()
            if isinstance(clause_terms[0], JoyQuotation):
                ctx.evaluator.execute(clause_terms[0])
            elif (
                isinstance(clause_terms[0], JoyValue)
                and clause_terms[0].type == JoyType.QUOTATION
            ):
                ctx.evaluator.execute(clause_terms[0].value)
            return

        # Regular clause: [condition body]
        # condition is first element, body is second
        condition = clause_terms[0]
        body = clause_terms[1] if len(clause_terms) > 1 else None

        # Test condition
        ctx.stack._items = saved.copy()
        if isinstance(condition, JoyQuotation):
            ctx.evaluator.execute(condition)
        elif isinstance(condition, JoyValue) and condition.type == JoyType.QUOTATION:
            ctx.evaluator.execute(condition.value)
        elif isinstance(condition, str):
            ctx.evaluator._execute_symbol(condition)
        else:
            ctx.stack.push_value(condition)

        test_result = ctx.stack.pop()

        if test_result.is_truthy():
            # Execute body
            ctx.stack._items = saved.copy()
            if body is not None:
                if isinstance(body, JoyQuotation):
                    ctx.evaluator.execute(body)
                elif isinstance(body, JoyValue) and body.type == JoyType.QUOTATION:
                    ctx.evaluator.execute(body.value)
                elif isinstance(body, str):
                    ctx.evaluator._execute_symbol(body)
            return

    # No clause matched, restore stack
    ctx.stack._items = saved


# ----------------------------------------------------------------------------
# Iteration Combinators
# ----------------------------------------------------------------------------


@joy_word(name="step", params=2, doc="A [P] -> ...")
def step(ctx: ExecutionContext) -> None:
    """Execute P for each element of A, pushing element before each call."""
    quot, agg = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "step")
    items = _get_aggregate(agg, "step")

    for item in items:
        ctx.stack.push_value(item)
        ctx.evaluator.execute(q)


@joy_word(name="map", params=2, doc="A [P] -> A'")
def map_combinator(ctx: ExecutionContext) -> None:
    """Apply P to each element of A, collecting results."""
    quot, agg = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "map")
    items = _get_aggregate(agg, "map")

    results = []
    for item in items:
        # Save stack
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(item)
        ctx.evaluator.execute(q)
        result = ctx.stack.pop()
        results.append(result)
        # Restore stack
        ctx.stack._items = saved

    ctx.stack.push_value(_make_aggregate(tuple(results), agg.type))


@joy_word(name="filter", params=2, doc="A [P] -> A'")
def filter_combinator(ctx: ExecutionContext) -> None:
    """Keep elements of A for which P returns true."""
    quot, agg = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "filter")
    items = _get_aggregate(agg, "filter")

    results = []
    for item in items:
        # Save stack
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(item)
        ctx.evaluator.execute(q)
        test_result = ctx.stack.pop()
        # Restore stack
        ctx.stack._items = saved

        if test_result.is_truthy():
            results.append(item)

    ctx.stack.push_value(_make_aggregate(tuple(results), agg.type))


@joy_word(name="fold", params=3, doc="A V [P] -> V'")
def fold(ctx: ExecutionContext) -> None:
    """Fold A with initial value V using binary operation P."""
    quot, init, agg = ctx.stack.pop_n(3)
    q = _expect_quotation(quot, "fold")
    items = _get_aggregate(agg, "fold")

    acc = init
    for item in items:
        ctx.stack.push_value(acc)
        ctx.stack.push_value(item)
        ctx.evaluator.execute(q)
        acc = ctx.stack.pop()

    ctx.stack.push_value(acc)


@joy_word(name="each", params=2, doc="A [P] -> ...")
def each(ctx: ExecutionContext) -> None:
    """Execute P for each element of A (alias for step)."""
    quot, agg = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "each")
    items = _get_aggregate(agg, "each")

    for item in items:
        ctx.stack.push_value(item)
        ctx.evaluator.execute(q)


@joy_word(name="any", params=2, doc="A [P] -> B")
def any_combinator(ctx: ExecutionContext) -> None:
    """Test if P is true for any element of A."""
    quot, agg = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "any")
    items = _get_aggregate(agg, "any")

    for item in items:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(item)
        ctx.evaluator.execute(q)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if test_result.is_truthy():
            ctx.stack.push_value(JoyValue.boolean(True))
            return

    ctx.stack.push_value(JoyValue.boolean(False))


@joy_word(name="all", params=2, doc="A [P] -> B")
def all_combinator(ctx: ExecutionContext) -> None:
    """Test if P is true for all elements of A."""
    quot, agg = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "all")
    items = _get_aggregate(agg, "all")

    for item in items:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(item)
        ctx.evaluator.execute(q)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if not test_result.is_truthy():
            ctx.stack.push_value(JoyValue.boolean(False))
            return

    ctx.stack.push_value(JoyValue.boolean(True))


# ----------------------------------------------------------------------------
# Looping Combinators
# ----------------------------------------------------------------------------


@joy_word(name="times", params=2, doc="N [P] -> ...")
def times(ctx: ExecutionContext) -> None:
    """Execute P exactly N times."""
    quot, n = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "times")
    if n.type != JoyType.INTEGER:
        raise JoyTypeError("times", "INTEGER", n.type.name)

    count = n.value
    for _ in range(count):
        ctx.evaluator.execute(q)


@joy_word(name="while", params=2, doc="[B] [P] -> ...")
def while_loop(ctx: ExecutionContext) -> None:
    """While B is true, execute P."""
    p_quot, b_quot = ctx.stack.pop_n(2)
    b = _expect_quotation(b_quot, "while")
    p = _expect_quotation(p_quot, "while")

    while True:
        # Save stack for condition test
        saved = ctx.stack._items.copy()
        ctx.evaluator.execute(b)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if not test_result.is_truthy():
            break

        ctx.evaluator.execute(p)


@joy_word(name="loop", params=1, doc="[P] -> ...")
def loop(ctx: ExecutionContext) -> None:
    """Execute P repeatedly until it leaves false on stack."""
    quot = ctx.stack.pop()
    q = _expect_quotation(quot, "loop")

    while True:
        ctx.evaluator.execute(q)
        test_result = ctx.stack.pop()
        if not test_result.is_truthy():
            break


# ----------------------------------------------------------------------------
# Additional Combinators (bi, tri, cleave)
# ----------------------------------------------------------------------------


@joy_word(name="bi", params=3, doc="X [P] [Q] -> ...")
def bi(ctx: ExecutionContext) -> None:
    """Apply P to X, then apply Q to X."""
    q_quot, p_quot, x = ctx.stack.pop_n(3)
    p = _expect_quotation(p_quot, "bi")
    q = _expect_quotation(q_quot, "bi")

    ctx.stack.push_value(x)
    ctx.evaluator.execute(p)
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)


@joy_word(name="tri", params=4, doc="X [P] [Q] [R] -> ...")
def tri(ctx: ExecutionContext) -> None:
    """Apply P, Q, R to X in sequence."""
    r_quot, q_quot, p_quot, x = ctx.stack.pop_n(4)
    p = _expect_quotation(p_quot, "tri")
    q = _expect_quotation(q_quot, "tri")
    r = _expect_quotation(r_quot, "tri")

    ctx.stack.push_value(x)
    ctx.evaluator.execute(p)
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)
    ctx.stack.push_value(x)
    ctx.evaluator.execute(r)


@joy_word(name="cleave", params=2, doc="X [P1 P2 ...] -> ...")
def cleave(ctx: ExecutionContext) -> None:
    """Apply each quotation in list to X."""
    quots, x = ctx.stack.pop_n(2)
    quot_list = _get_aggregate(quots, "cleave")

    for q_val in quot_list:
        if isinstance(q_val, JoyValue) and q_val.type == JoyType.QUOTATION:
            ctx.stack.push_value(x)
            ctx.evaluator.execute(q_val.value)
        elif isinstance(q_val, JoyQuotation):
            ctx.stack.push_value(x)
            ctx.evaluator.execute(q_val)


@joy_word(name="spread", params=2, doc="X Y ... [P1 P2 ...] -> ...")
def spread(ctx: ExecutionContext) -> None:
    """Apply P1 to X, P2 to Y, etc."""
    quots = ctx.stack.pop()
    quot_list = _get_aggregate(quots, "spread")

    if not quot_list:
        return

    # Pop values for each quotation
    values = list(ctx.stack.pop_n(len(quot_list)))
    values.reverse()  # So first value pairs with first quotation

    for val, q_val in zip(values, quot_list):
        if isinstance(q_val, JoyValue) and q_val.type == JoyType.QUOTATION:
            ctx.stack.push_value(val)
            ctx.evaluator.execute(q_val.value)
        elif isinstance(q_val, JoyQuotation):
            ctx.stack.push_value(val)
            ctx.evaluator.execute(q_val)


@joy_word(name="infra", params=2, doc="L [P] -> L'")
def infra(ctx: ExecutionContext) -> None:
    """Execute P with L as the stack, return new stack as list."""
    quot, lst = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "infra")
    items = _get_aggregate(lst, "infra")

    # Save current stack
    saved = ctx.stack._items.copy()

    # Replace stack with list contents
    ctx.stack._items = list(items)

    # Execute quotation
    ctx.evaluator.execute(q)

    # Collect result as list
    result = tuple(ctx.stack._items)

    # Restore original stack and push result
    ctx.stack._items = saved
    ctx.stack.push_value(JoyValue.list(result))


@joy_word(name="app1", params=2, doc="X [P] -> X'")
def app1(ctx: ExecutionContext) -> None:
    """Apply P to X, leaving result (like unary but different semantics)."""
    quot, x = ctx.stack.pop_n(2)
    q = _expect_quotation(quot, "app1")
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)


@joy_word(name="app2", params=3, doc="X Y [P] -> X' Y'")
def app2(ctx: ExecutionContext) -> None:
    """Apply P to X and Y separately, leaving both results."""
    quot, y, x = ctx.stack.pop_n(3)
    q = _expect_quotation(quot, "app2")

    # Apply to X
    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)
    x_result = ctx.stack.pop()
    ctx.stack._items = saved

    # Apply to Y
    saved = ctx.stack._items.copy()
    ctx.stack.push_value(y)
    ctx.evaluator.execute(q)
    y_result = ctx.stack.pop()
    ctx.stack._items = saved

    ctx.stack.push_value(x_result)
    ctx.stack.push_value(y_result)


@joy_word(name="app3", params=4, doc="X Y Z [P] -> X' Y' Z'")
def app3(ctx: ExecutionContext) -> None:
    """Apply P to X, Y, Z separately, leaving all results."""
    quot, z, y, x = ctx.stack.pop_n(4)
    q = _expect_quotation(quot, "app3")

    results = []
    for val in [x, y, z]:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(val)
        ctx.evaluator.execute(q)
        results.append(ctx.stack.pop())
        ctx.stack._items = saved

    for r in results:
        ctx.stack.push_value(r)


@joy_word(name="compose", params=2, doc="[P] [Q] -> [[P] [Q] concat]")
def compose(ctx: ExecutionContext) -> None:
    """Compose two quotations into one."""
    q2, q1 = ctx.stack.pop_n(2)
    p1 = _expect_quotation(q1, "compose")
    p2 = _expect_quotation(q2, "compose")

    # Create combined quotation
    combined = JoyQuotation(p1.terms + p2.terms)
    ctx.stack.push_value(JoyValue.quotation(combined))


# =============================================================================
# Phase 4: Recursion Combinators
# =============================================================================


@joy_word(name="primrec", params=3, doc="X [I] [C] -> R")
def primrec(ctx: ExecutionContext) -> None:
    """
    Primitive recursion.

    Executes I to obtain an initial value R0.
    For integer X: uses increasing positive integers to X, combines by C for new R.
    For aggregate X: uses successive members and combines by C for new R.
    """
    c_quot, i_quot, x = ctx.stack.pop_n(3)
    i = _expect_quotation(i_quot, "primrec")
    c = _expect_quotation(c_quot, "primrec")

    # Execute I to get initial value
    ctx.evaluator.execute(i)
    # Result is now on stack

    if x.type == JoyType.INTEGER:
        # For integer: combine with 1, 2, ..., X
        n = x.value
        for j in range(1, n + 1):
            ctx.stack.push(j)
            ctx.evaluator.execute(c)
    elif x.type in (JoyType.LIST, JoyType.QUOTATION):
        # For aggregate: combine with each member
        items = x.value if x.type == JoyType.LIST else x.value.terms
        for item in items:
            if isinstance(item, JoyValue):
                ctx.stack.push_value(item)
            else:
                ctx.stack.push(item)
            ctx.evaluator.execute(c)
    elif x.type == JoyType.STRING:
        # For string: combine with each character
        for ch in x.value:
            ctx.stack.push(ch)
            ctx.evaluator.execute(c)
    elif x.type == JoyType.SET:
        # For set: combine with each member
        for member in sorted(x.value):
            ctx.stack.push(member)
            ctx.evaluator.execute(c)
    else:
        raise JoyTypeError(f"primrec: expected integer or aggregate, got {x.type}")


@joy_word(name="linrec", params=4, doc="[P] [T] [R1] [R2] -> ...")
def linrec(ctx: ExecutionContext) -> None:
    """
    Linear recursion combinator.

    [P] = predicate (if-base-case)
    [T] = terminal (base case)
    [R1] = reduce (before recursion)
    [R2] = combine (after recursion)

    Executes P. If that yields true, executes T.
    Else executes R1, recurses, executes R2.
    """
    r2_quot, r1_quot, t_quot, p_quot = ctx.stack.pop_n(4)
    p = _expect_quotation(p_quot, "linrec")
    t = _expect_quotation(t_quot, "linrec")
    r1 = _expect_quotation(r1_quot, "linrec")
    r2 = _expect_quotation(r2_quot, "linrec")

    def linrec_aux() -> None:
        # Save stack state for predicate test
        saved = ctx.stack._items.copy()

        # Execute predicate
        ctx.evaluator.execute(p)
        test_result = ctx.stack.pop()

        # Restore stack
        ctx.stack._items = saved

        if test_result.is_truthy():
            # Base case: execute terminal
            ctx.evaluator.execute(t)
        else:
            # Recursive case: execute R1, recurse, execute R2
            ctx.evaluator.execute(r1)
            linrec_aux()
            ctx.evaluator.execute(r2)

    linrec_aux()


@joy_word(name="binrec", params=4, doc="[P] [T] [R1] [R2] -> ...")
def binrec(ctx: ExecutionContext) -> None:
    """
    Binary recursion combinator (divide and conquer).

    [P] = predicate (if-base-case)
    [T] = terminal (base case)
    [R1] = split (produces two values)
    [R2] = combine (combines two results)

    Executes P. If that yields true, executes T.
    Else uses R1 to produce two intermediates, recurses on both,
    then executes R2 to combine their results.
    """
    r2_quot, r1_quot, t_quot, p_quot = ctx.stack.pop_n(4)
    p = _expect_quotation(p_quot, "binrec")
    t = _expect_quotation(t_quot, "binrec")
    r1 = _expect_quotation(r1_quot, "binrec")
    r2 = _expect_quotation(r2_quot, "binrec")

    def binrec_aux() -> None:
        # Save stack state for predicate test
        saved = ctx.stack._items.copy()

        # Execute predicate
        ctx.evaluator.execute(p)
        test_result = ctx.stack.pop()

        # Restore stack
        ctx.stack._items = saved

        if test_result.is_truthy():
            # Base case: execute terminal
            ctx.evaluator.execute(t)
        else:
            # Split into two
            ctx.evaluator.execute(r1)

            # Save first result (top of stack)
            first_arg = ctx.stack.pop()

            # Recurse on remaining (what's still on stack)
            binrec_aux()
            first_result = ctx.stack.pop()

            # Restore first arg and recurse on it
            ctx.stack.push_value(first_arg)
            binrec_aux()

            # Push first result back
            ctx.stack.push_value(first_result)

            # Combine
            ctx.evaluator.execute(r2)

    binrec_aux()


@joy_word(name="tailrec", params=3, doc="[P] [T] [R1] -> ...")
def tailrec(ctx: ExecutionContext) -> None:
    """
    Tail recursion combinator.

    [P] = predicate (if-base-case)
    [T] = terminal (base case)
    [R1] = recurse (prepare for next iteration)

    Executes P. If that yields true, executes T.
    Else executes R1, recurses.
    """
    r1_quot, t_quot, p_quot = ctx.stack.pop_n(3)
    p = _expect_quotation(p_quot, "tailrec")
    t = _expect_quotation(t_quot, "tailrec")
    r1 = _expect_quotation(r1_quot, "tailrec")

    # Use iteration instead of actual recursion for tail-call optimization
    while True:
        # Save stack state for predicate test
        saved = ctx.stack._items.copy()

        # Execute predicate
        ctx.evaluator.execute(p)
        test_result = ctx.stack.pop()

        # Restore stack
        ctx.stack._items = saved

        if test_result.is_truthy():
            # Base case: execute terminal and exit
            ctx.evaluator.execute(t)
            break
        else:
            # Execute R1 and continue loop
            ctx.evaluator.execute(r1)


@joy_word(name="genrec", params=4, doc="[B] [T] [R1] [R2] -> ...")
def genrec(ctx: ExecutionContext) -> None:
    """
    General recursion combinator.

    [B] = predicate (if-base-case)
    [T] = terminal (base case)
    [R1] = pre-recursion
    [R2] = post-recursion

    Executes B. If that yields true, executes T.
    Else executes R1 and then [[B] [T] [R1] R2] genrec] R2.

    This is the most general recursion combinator. The key insight is that
    R2 has access to a quotation that contains the recursive call.
    """
    r2_quot, r1_quot, t_quot, b_quot = ctx.stack.pop_n(4)
    b = _expect_quotation(b_quot, "genrec")
    t = _expect_quotation(t_quot, "genrec")
    r1 = _expect_quotation(r1_quot, "genrec")
    r2 = _expect_quotation(r2_quot, "genrec")

    def genrec_aux() -> None:
        # Save stack state for predicate test
        saved = ctx.stack._items.copy()

        # Execute predicate B
        ctx.evaluator.execute(b)
        test_result = ctx.stack.pop()

        # Restore stack
        ctx.stack._items = saved

        if test_result.is_truthy():
            # Base case: execute terminal
            ctx.evaluator.execute(t)
        else:
            # Execute R1
            ctx.evaluator.execute(r1)

            # Build the recursive quotation: [[B] [T] [R1] R2] genrec
            # This quotation, when executed, will call genrec_aux
            # We create a quotation that captures the continuation
            rec_quot = JoyQuotation(
                (
                    JoyValue.quotation(b),
                    JoyValue.quotation(t),
                    JoyValue.quotation(r1),
                    JoyValue.quotation(r2),
                    "genrec",
                )
            )
            ctx.stack.push_value(JoyValue.quotation(rec_quot))

            # Execute R2 (which typically uses the recursive quotation)
            ctx.evaluator.execute(r2)

    genrec_aux()


# =============================================================================
# Phase 5: I/O and System Operations
# =============================================================================

import io as io_module
import os
import sys
import time as time_module

# -----------------------------------------------------------------------------
# Output Primitives
# -----------------------------------------------------------------------------


@joy_word(name="put", params=1, doc="X ->")
def put(ctx: ExecutionContext) -> None:
    """Write X to output, then pop X off stack."""
    x = ctx.stack.pop()
    # Write the Joy representation
    print(repr(x), end="")


@joy_word(name="putch", params=1, doc="N ->")
def putch(ctx: ExecutionContext) -> None:
    """Write character whose ASCII/Unicode is N."""
    n = ctx.stack.pop()
    if n.type == JoyType.INTEGER:
        print(chr(n.value), end="")
    elif n.type == JoyType.CHAR:
        print(n.value, end="")
    else:
        raise JoyTypeError("putch", "integer or char", n.type.name)


@joy_word(name="putchars", params=1, doc="S ->")
def putchars(ctx: ExecutionContext) -> None:
    """Write string S (without quotes)."""
    s = ctx.stack.pop()
    if s.type != JoyType.STRING:
        raise JoyTypeError("putchars", "string", s.type.name)
    print(s.value, end="")


@joy_word(name="newline", params=0, doc="->")
def newline(ctx: ExecutionContext) -> None:
    """Write a newline character."""
    print()


# -----------------------------------------------------------------------------
# Input Primitives
# -----------------------------------------------------------------------------


@joy_word(name="get", params=0, doc="-> F")
def get(ctx: ExecutionContext) -> None:
    """Read a factor from input and push it onto stack."""

    line = input()
    program = parse(line)
    # Push all terms from parsed input
    for term in program.terms:
        if isinstance(term, JoyValue):
            ctx.stack.push_value(term)
        elif isinstance(term, str):
            # Symbol - look it up or treat as string
            ctx.stack.push(term)
        else:
            ctx.stack.push(term)


@joy_word(name="getch", params=0, doc="-> C")
def getch(ctx: ExecutionContext) -> None:
    """Read a single character from input."""
    ch = sys.stdin.read(1)
    if ch:
        ctx.stack.push_value(JoyValue.char(ch))
    else:
        ctx.stack.push_value(JoyValue.integer(-1))  # EOF


@joy_word(name="getline", params=0, doc="-> S")
def getline(ctx: ExecutionContext) -> None:
    """Read a line from input (without newline)."""
    try:
        line = input()
        ctx.stack.push_value(JoyValue.string(line))
    except EOFError:
        ctx.stack.push_value(JoyValue.string(""))


# -----------------------------------------------------------------------------
# Standard Streams
# -----------------------------------------------------------------------------


@joy_word(name="stdin", params=0, doc="-> S")
def stdin_(ctx: ExecutionContext) -> None:
    """Push the standard input stream."""
    ctx.stack.push_value(JoyValue.file(sys.stdin))


@joy_word(name="stdout", params=0, doc="-> S")
def stdout_(ctx: ExecutionContext) -> None:
    """Push the standard output stream."""
    ctx.stack.push_value(JoyValue.file(sys.stdout))


@joy_word(name="stderr", params=0, doc="-> S")
def stderr_(ctx: ExecutionContext) -> None:
    """Push the standard error stream."""
    ctx.stack.push_value(JoyValue.file(sys.stderr))


# -----------------------------------------------------------------------------
# File Operations
# -----------------------------------------------------------------------------


def _expect_file(v: JoyValue, op: str) -> io_module.IOBase:
    """Extract file handle from JoyValue."""
    if v.type != JoyType.FILE:
        raise JoyTypeError(op, "file", v.type.name)
    if v.value is None:
        raise JoyTypeError(op, "open file", "NULL file")
    return v.value


@joy_word(name="fopen", params=2, doc="P M -> S")
def fopen(ctx: ExecutionContext) -> None:
    """Open file with pathname P and mode M, push stream S."""
    mode, path = ctx.stack.pop_n(2)
    if path.type != JoyType.STRING:
        raise JoyTypeError("fopen", "string (path)", path.type.name)
    if mode.type != JoyType.STRING:
        raise JoyTypeError("fopen", "string (mode)", mode.type.name)

    try:
        # Handle binary modes
        if "b" in mode.value:
            f = open(path.value, mode.value)
        else:
            f = open(path.value, mode.value, encoding="utf-8")
        ctx.stack.push_value(JoyValue.file(f))
    except (OSError, IOError):
        # Push NULL file on failure
        ctx.stack.push_value(JoyValue.file(None))


@joy_word(name="fclose", params=1, doc="S ->")
def fclose(ctx: ExecutionContext) -> None:
    """Close stream S and remove from stack."""
    s = ctx.stack.pop()
    f = _expect_file(s, "fclose")
    if f not in (sys.stdin, sys.stdout, sys.stderr):
        f.close()


@joy_word(name="fread", params=2, doc="S I -> S L")
def fread(ctx: ExecutionContext) -> None:
    """Read I bytes from stream S, return as list of integers."""
    count, stream = ctx.stack.pop_n(2)
    f = _expect_file(stream, "fread")
    if count.type != JoyType.INTEGER:
        raise JoyTypeError("fread", "integer", count.type.name)

    data = f.read(count.value)
    if isinstance(data, str):
        # Text mode - convert to bytes
        data = data.encode("utf-8")

    result = tuple(JoyValue.integer(b) for b in data)
    ctx.stack.push_value(stream)
    ctx.stack.push_value(JoyValue.list(result))


@joy_word(name="fwrite", params=2, doc="S L -> S")
def fwrite(ctx: ExecutionContext) -> None:
    """Write list of integers as bytes to stream S."""
    lst, stream = ctx.stack.pop_n(2)
    f = _expect_file(stream, "fwrite")
    if lst.type not in (JoyType.LIST, JoyType.QUOTATION):
        raise JoyTypeError("fwrite", "list", lst.type.name)

    items = lst.value if lst.type == JoyType.LIST else lst.value.terms
    data = bytes(int(item.value) & 0xFF for item in items if isinstance(item, JoyValue))

    if hasattr(f, "mode") and "b" in f.mode:
        f.write(data)
    else:
        f.write(data.decode("utf-8", errors="replace"))

    ctx.stack.push_value(stream)


@joy_word(name="fflush", params=1, doc="S -> S")
def fflush(ctx: ExecutionContext) -> None:
    """Flush stream S."""
    stream = ctx.stack.peek()
    f = _expect_file(stream, "fflush")
    f.flush()


@joy_word(name="feof", params=1, doc="S -> S B")
def feof(ctx: ExecutionContext) -> None:
    """Test if stream S is at end of file."""
    stream = ctx.stack.peek()
    f = _expect_file(stream, "feof")
    # Try to check EOF by reading and putting back
    pos = f.tell() if hasattr(f, "tell") and f.seekable() else None
    ch = f.read(1)
    at_eof = len(ch) == 0
    if pos is not None and not at_eof:
        f.seek(pos)
    ctx.stack.push_value(JoyValue.boolean(at_eof))


@joy_word(name="ftell", params=1, doc="S -> S I")
def ftell(ctx: ExecutionContext) -> None:
    """Get current position in stream S."""
    stream = ctx.stack.peek()
    f = _expect_file(stream, "ftell")
    pos = f.tell() if hasattr(f, "tell") else 0
    ctx.stack.push_value(JoyValue.integer(pos))


@joy_word(name="fseek", params=3, doc="S I W -> S")
def fseek(ctx: ExecutionContext) -> None:
    """Seek to position I in stream S with whence W."""
    whence, pos, stream = ctx.stack.pop_n(3)
    f = _expect_file(stream, "fseek")
    if pos.type != JoyType.INTEGER:
        raise JoyTypeError("fseek", "integer (position)", pos.type.name)
    if whence.type != JoyType.INTEGER:
        raise JoyTypeError("fseek", "integer (whence)", whence.type.name)

    f.seek(pos.value, whence.value)
    ctx.stack.push_value(stream)


@joy_word(name="fputch", params=2, doc="S C -> S")
def fputch(ctx: ExecutionContext) -> None:
    """Write character C to stream S."""
    ch, stream = ctx.stack.pop_n(2)
    f = _expect_file(stream, "fputch")

    if ch.type == JoyType.INTEGER:
        f.write(chr(ch.value))
    elif ch.type == JoyType.CHAR:
        f.write(ch.value)
    else:
        raise JoyTypeError("fputch", "integer or char", ch.type.name)

    ctx.stack.push_value(stream)


@joy_word(name="fgetch", params=1, doc="S -> S C")
def fgetch(ctx: ExecutionContext) -> None:
    """Read a character from stream S."""
    stream = ctx.stack.peek()
    f = _expect_file(stream, "fgetch")
    ch = f.read(1)
    if ch:
        ctx.stack.push_value(JoyValue.char(ch))
    else:
        ctx.stack.push_value(JoyValue.integer(-1))  # EOF


@joy_word(name="fputchars", params=2, doc="S A -> S")
def fputchars(ctx: ExecutionContext) -> None:
    """Write string/list A to stream S."""
    agg, stream = ctx.stack.pop_n(2)
    f = _expect_file(stream, "fputchars")

    if agg.type == JoyType.STRING:
        f.write(agg.value)
    elif agg.type in (JoyType.LIST, JoyType.QUOTATION):
        items = agg.value if agg.type == JoyType.LIST else agg.value.terms
        for item in items:
            if isinstance(item, JoyValue):
                if item.type == JoyType.CHAR:
                    f.write(item.value)
                elif item.type == JoyType.INTEGER:
                    f.write(chr(item.value))
    else:
        raise JoyTypeError("fputchars", "string or list", agg.type.name)

    ctx.stack.push_value(stream)


@joy_word(name="fgets", params=1, doc="S -> S L")
def fgets(ctx: ExecutionContext) -> None:
    """Read a line from stream S."""
    stream = ctx.stack.peek()
    f = _expect_file(stream, "fgets")
    line = f.readline()
    ctx.stack.push_value(JoyValue.string(line))


# -----------------------------------------------------------------------------
# System Operations
# -----------------------------------------------------------------------------


@joy_word(name="time", params=0, doc="-> I")
def time_(ctx: ExecutionContext) -> None:
    """Push current time in seconds since Epoch."""
    ctx.stack.push_value(JoyValue.integer(int(time_module.time())))


@joy_word(name="clock", params=0, doc="-> I")
def clock(ctx: ExecutionContext) -> None:
    """Push CPU time in microseconds."""
    ctx.stack.push_value(JoyValue.integer(int(time_module.perf_counter() * 1_000_000)))


@joy_word(name="getenv", params=1, doc="S -> S")
def getenv_(ctx: ExecutionContext) -> None:
    """Get environment variable value."""
    name = ctx.stack.pop()
    if name.type != JoyType.STRING:
        raise JoyTypeError("getenv", "string", name.type.name)

    value = os.environ.get(name.value, "")
    ctx.stack.push_value(JoyValue.string(value))


@joy_word(name="system", params=1, doc="S -> I")
def system_(ctx: ExecutionContext) -> None:
    """Execute system command, return exit code."""
    cmd = ctx.stack.pop()
    if cmd.type != JoyType.STRING:
        raise JoyTypeError("system", "string", cmd.type.name)

    exit_code = os.system(cmd.value)
    ctx.stack.push_value(JoyValue.integer(exit_code))


@joy_word(name="argc", params=0, doc="-> I")
def argc_(ctx: ExecutionContext) -> None:
    """Push number of command line arguments."""
    ctx.stack.push_value(JoyValue.integer(len(sys.argv)))


@joy_word(name="argv", params=0, doc="-> L")
def argv_(ctx: ExecutionContext) -> None:
    """Push list of command line arguments."""
    args = tuple(JoyValue.string(arg) for arg in sys.argv)
    ctx.stack.push_value(JoyValue.list(args))


@joy_word(name="abort", params=0, doc="->")
def abort_(ctx: ExecutionContext) -> None:
    """Abort execution with error."""
    raise SystemExit(1)


@joy_word(name="quit", params=1, doc="I ->")
def quit_(ctx: ExecutionContext) -> None:
    """Exit with status code I."""
    code = ctx.stack.pop()
    if code.type != JoyType.INTEGER:
        raise JoyTypeError("quit", "integer", code.type.name)
    raise SystemExit(code.value)


# -----------------------------------------------------------------------------
# Formatting
# -----------------------------------------------------------------------------


@joy_word(name="format", params=4, doc="N C I J -> S")
def format_(ctx: ExecutionContext) -> None:
    """
    Format N in mode C with max width I and min width J.

    C is a character: 'd' or 'i' = decimal, 'o' = octal, 'x' or 'X' = hex.
    """
    j, i, c, n = ctx.stack.pop_n(4)

    if n.type not in (JoyType.INTEGER, JoyType.FLOAT):
        raise JoyTypeError("format", "numeric", n.type.name)
    if c.type not in (JoyType.CHAR, JoyType.INTEGER):
        raise JoyTypeError("format", "char", c.type.name)
    if i.type != JoyType.INTEGER:
        raise JoyTypeError("format", "integer (width)", i.type.name)
    if j.type != JoyType.INTEGER:
        raise JoyTypeError("format", "integer (precision)", j.type.name)

    spec = chr(c.value) if c.type == JoyType.INTEGER else c.value
    width = i.value
    prec = j.value

    if spec in ("d", "i"):
        result = (
            f"{int(n.value):*>{width}.{prec}d}" if prec else f"{int(n.value):>{width}d}"
        )
    elif spec == "o":
        result = f"{int(n.value):>{width}o}"
    elif spec == "x":
        result = f"{int(n.value):>{width}x}"
    elif spec == "X":
        result = f"{int(n.value):>{width}X}"
    elif spec == "f":
        result = f"{float(n.value):>{width}.{prec}f}"
    elif spec == "e":
        result = f"{float(n.value):>{width}.{prec}e}"
    else:
        result = str(n.value)

    ctx.stack.push_value(JoyValue.string(result))


@joy_word(name="formatf", params=2, doc="F S -> S")
def formatf(ctx: ExecutionContext) -> None:
    """Format float F using format string S."""
    fmt, f = ctx.stack.pop_n(2)
    if f.type not in (JoyType.FLOAT, JoyType.INTEGER):
        raise JoyTypeError("formatf", "numeric", f.type.name)
    if fmt.type != JoyType.STRING:
        raise JoyTypeError("formatf", "string", fmt.type.name)

    try:
        result = fmt.value % float(f.value)
    except (ValueError, TypeError):
        result = str(f.value)

    ctx.stack.push_value(JoyValue.string(result))


# -----------------------------------------------------------------------------
# String Utilities
# -----------------------------------------------------------------------------


@joy_word(name="strtol", params=2, doc="S I -> N")
def strtol(ctx: ExecutionContext) -> None:
    """Convert string S to integer in base I."""
    base, s = ctx.stack.pop_n(2)
    if s.type != JoyType.STRING:
        raise JoyTypeError("strtol", "string", s.type.name)
    if base.type != JoyType.INTEGER:
        raise JoyTypeError("strtol", "integer (base)", base.type.name)

    try:
        result = int(s.value, base.value)
        ctx.stack.push_value(JoyValue.integer(result))
    except ValueError:
        ctx.stack.push_value(JoyValue.integer(0))


@joy_word(name="strtod", params=1, doc="S -> F")
def strtod(ctx: ExecutionContext) -> None:
    """Convert string S to float."""
    s = ctx.stack.pop()
    if s.type != JoyType.STRING:
        raise JoyTypeError("strtod", "string", s.type.name)

    try:
        result = float(s.value)
        ctx.stack.push_value(JoyValue.floating(result))
    except ValueError:
        ctx.stack.push_value(JoyValue.floating(0.0))


@joy_word(name="intern", params=1, doc="S -> A")
def intern_(ctx: ExecutionContext) -> None:
    """Convert string S to symbol (interned atom)."""
    s = ctx.stack.pop()
    if s.type != JoyType.STRING:
        raise JoyTypeError("intern", "string", s.type.name)
    ctx.stack.push_value(JoyValue.symbol(s.value))


@joy_word(name="name", params=1, doc="A -> S")
def name_(ctx: ExecutionContext) -> None:
    """Convert atom/symbol to string."""
    a = ctx.stack.pop()
    if a.type == JoyType.SYMBOL:
        ctx.stack.push_value(JoyValue.string(a.value))
    else:
        ctx.stack.push_value(JoyValue.string(repr(a)))
