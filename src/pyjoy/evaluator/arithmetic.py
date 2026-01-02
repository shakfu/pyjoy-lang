"""
pyjoy.evaluator.arithmetic - Arithmetic and math primitives.

Contains: +, -, *, /, rem, div, abs, neg, sign, succ, pred, max, min,
and all math functions (sin, cos, tan, sqrt, pow, etc.)
"""

from __future__ import annotations

import math as _math
import random as _random

from pyjoy.errors import JoyDivisionByZero, JoyTypeError
from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyType, JoyValue

from .core import joy_word


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


# -----------------------------------------------------------------------------
# Basic Arithmetic
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# Math Functions
# -----------------------------------------------------------------------------


@joy_word(name="sin", params=1, doc="F -> F")
def sin_(ctx: ExecutionContext) -> None:
    """Sine of F (radians)."""
    a = ctx.stack.pop()
    result = _math.sin(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="cos", params=1, doc="F -> F")
def cos_(ctx: ExecutionContext) -> None:
    """Cosine of F (radians)."""
    a = ctx.stack.pop()
    result = _math.cos(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="tan", params=1, doc="F -> F")
def tan_(ctx: ExecutionContext) -> None:
    """Tangent of F (radians)."""
    a = ctx.stack.pop()
    result = _math.tan(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="asin", params=1, doc="F -> F")
def asin_(ctx: ExecutionContext) -> None:
    """Arc sine of F."""
    a = ctx.stack.pop()
    result = _math.asin(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="acos", params=1, doc="F -> F")
def acos_(ctx: ExecutionContext) -> None:
    """Arc cosine of F."""
    a = ctx.stack.pop()
    result = _math.acos(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="atan", params=1, doc="F -> F")
def atan_(ctx: ExecutionContext) -> None:
    """Arc tangent of F."""
    a = ctx.stack.pop()
    result = _math.atan(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="atan2", params=2, doc="F G -> F")
def atan2_(ctx: ExecutionContext) -> None:
    """Arc tangent of F/G using signs to determine quadrant."""
    b, a = ctx.stack.pop_n(2)
    result = _math.atan2(_numeric_value(a), _numeric_value(b))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="sinh", params=1, doc="F -> F")
def sinh_(ctx: ExecutionContext) -> None:
    """Hyperbolic sine of F."""
    a = ctx.stack.pop()
    result = _math.sinh(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="cosh", params=1, doc="F -> F")
def cosh_(ctx: ExecutionContext) -> None:
    """Hyperbolic cosine of F."""
    a = ctx.stack.pop()
    result = _math.cosh(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="tanh", params=1, doc="F -> F")
def tanh_(ctx: ExecutionContext) -> None:
    """Hyperbolic tangent of F."""
    a = ctx.stack.pop()
    result = _math.tanh(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="exp", params=1, doc="F -> F")
def exp_(ctx: ExecutionContext) -> None:
    """e raised to the power F."""
    a = ctx.stack.pop()
    result = _math.exp(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="log", params=1, doc="F -> F")
def log_(ctx: ExecutionContext) -> None:
    """Natural logarithm of F."""
    a = ctx.stack.pop()
    result = _math.log(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="log10", params=1, doc="F -> F")
def log10_(ctx: ExecutionContext) -> None:
    """Base-10 logarithm of F."""
    a = ctx.stack.pop()
    result = _math.log10(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="sqrt", params=1, doc="F -> F")
def sqrt_(ctx: ExecutionContext) -> None:
    """Square root of F."""
    a = ctx.stack.pop()
    result = _math.sqrt(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="pow", params=2, doc="F G -> F")
def pow_(ctx: ExecutionContext) -> None:
    """F raised to the power G."""
    b, a = ctx.stack.pop_n(2)
    result = _math.pow(_numeric_value(a), _numeric_value(b))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="ceil", params=1, doc="F -> F")
def ceil_(ctx: ExecutionContext) -> None:
    """Ceiling of F."""
    a = ctx.stack.pop()
    result = _math.ceil(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(float(result)))


@joy_word(name="floor", params=1, doc="F -> F")
def floor_(ctx: ExecutionContext) -> None:
    """Floor of F."""
    a = ctx.stack.pop()
    result = _math.floor(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(float(result)))


@joy_word(name="trunc", params=1, doc="F -> F")
def trunc_(ctx: ExecutionContext) -> None:
    """Truncate F toward zero."""
    a = ctx.stack.pop()
    result = _math.trunc(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(float(result)))


@joy_word(name="round", params=1, doc="F -> F")
def round_(ctx: ExecutionContext) -> None:
    """Round F to nearest integer."""
    a = ctx.stack.pop()
    result = round(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(float(result)))


@joy_word(name="frexp", params=1, doc="F -> F I")
def frexp_(ctx: ExecutionContext) -> None:
    """Split F into mantissa and exponent: F = mantissa * 2^exponent."""
    a = ctx.stack.pop()
    mantissa, exponent = _math.frexp(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(mantissa))
    ctx.stack.push_value(JoyValue.integer(exponent))


@joy_word(name="ldexp", params=2, doc="F I -> F")
def ldexp_(ctx: ExecutionContext) -> None:
    """Compute F * 2^I."""
    b, a = ctx.stack.pop_n(2)
    result = _math.ldexp(_numeric_value(a), int(_numeric_value(b)))
    ctx.stack.push_value(JoyValue.floating(result))


@joy_word(name="modf", params=1, doc="F -> F F")
def modf_(ctx: ExecutionContext) -> None:
    """Split F into fractional and integer parts."""
    a = ctx.stack.pop()
    frac, integer = _math.modf(_numeric_value(a))
    ctx.stack.push_value(JoyValue.floating(frac))
    ctx.stack.push_value(JoyValue.floating(integer))


# -----------------------------------------------------------------------------
# Random Number Generation
# -----------------------------------------------------------------------------


@joy_word(name="rand", params=0, doc="-> I")
def rand_(ctx: ExecutionContext) -> None:
    """Push a random integer."""
    ctx.stack.push_value(JoyValue.integer(_random.randint(0, 2**31 - 1)))


@joy_word(name="srand", params=1, doc="I ->")
def srand_(ctx: ExecutionContext) -> None:
    """Seed the random number generator."""
    seed = ctx.stack.pop()
    if seed.type != JoyType.INTEGER:
        raise JoyTypeError("srand", "INTEGER", seed.type.name)
    _random.seed(seed.value)
