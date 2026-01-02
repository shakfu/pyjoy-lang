"""
pyjoy.evaluator.types - Type predicates and conditionals.

Contains type predicates: integer, float, char, string, list, logical, set,
leaf, file, user, sametype, typeof

Contains type conditionals: ifinteger, ifchar, iflogical, ifset, ifstring,
iflist, iffloat, iffile
"""

from __future__ import annotations

from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyType, JoyValue

from .core import expect_quotation, joy_word


# -----------------------------------------------------------------------------
# Type Predicates
# -----------------------------------------------------------------------------


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


@joy_word(name="set", params=1, doc="X -> B")
def is_set(ctx: ExecutionContext) -> None:
    """Test if X is a set."""
    x = ctx.stack.pop()
    ctx.stack.push_value(JoyValue.boolean(x.type == JoyType.SET))


@joy_word(name="leaf", params=1, doc="X -> B")
def is_leaf(ctx: ExecutionContext) -> None:
    """Test if X is an atom (not a list or quotation)."""
    x = ctx.stack.pop()
    is_aggregate = x.type in (JoyType.LIST, JoyType.QUOTATION)
    ctx.stack.push_value(JoyValue.boolean(not is_aggregate))


@joy_word(name="file", params=1, doc="X -> B")
def is_file(ctx: ExecutionContext) -> None:
    """Test if X is a file handle."""
    x = ctx.stack.pop()
    ctx.stack.push_value(JoyValue.boolean(x.type == JoyType.FILE))


@joy_word(name="user", params=1, doc="X -> B")
def is_user(ctx: ExecutionContext) -> None:
    """Test if X is a user-defined symbol."""
    x = ctx.stack.pop()
    if x.type != JoyType.SYMBOL:
        ctx.stack.push_value(JoyValue.boolean(False))
    else:
        is_defined = x.value in ctx.evaluator.definitions
        ctx.stack.push_value(JoyValue.boolean(is_defined))


@joy_word(name="sametype", params=2, doc="X Y -> B")
def sametype(ctx: ExecutionContext) -> None:
    """Test if X and Y have the same type."""
    b, a = ctx.stack.pop_n(2)
    ctx.stack.push_value(JoyValue.boolean(a.type == b.type))


@joy_word(name="typeof", params=1, doc="X -> I")
def typeof_(ctx: ExecutionContext) -> None:
    """Return type of X as integer."""
    x = ctx.stack.pop()
    # Joy type codes: 0=list, 1=bool, 2=char, 3=int, 4=set, 5=string, 6=symbol, 7=float, 8=file
    type_codes = {
        JoyType.LIST: 0,
        JoyType.BOOLEAN: 1,
        JoyType.CHAR: 2,
        JoyType.INTEGER: 3,
        JoyType.SET: 4,
        JoyType.STRING: 5,
        JoyType.SYMBOL: 6,
        JoyType.FLOAT: 7,
        JoyType.FILE: 8,
        JoyType.QUOTATION: 0,  # Quotation treated as list
    }
    ctx.stack.push_value(JoyValue.integer(type_codes.get(x.type, -1)))


# -----------------------------------------------------------------------------
# Type Conditionals
# -----------------------------------------------------------------------------


@joy_word(name="ifinteger", params=3, doc="X [T] [F] -> ...")
def ifinteger(ctx: ExecutionContext) -> None:
    """Execute T if X is integer, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(x)
    if x.type == JoyType.INTEGER:
        ctx.evaluator.execute(expect_quotation(t_quot, "ifinteger"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "ifinteger"))


@joy_word(name="ifchar", params=3, doc="X [T] [F] -> ...")
def ifchar(ctx: ExecutionContext) -> None:
    """Execute T if X is char, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(x)
    if x.type == JoyType.CHAR:
        ctx.evaluator.execute(expect_quotation(t_quot, "ifchar"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "ifchar"))


@joy_word(name="iflogical", params=3, doc="X [T] [F] -> ...")
def iflogical(ctx: ExecutionContext) -> None:
    """Execute T if X is boolean, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(x)
    if x.type == JoyType.BOOLEAN:
        ctx.evaluator.execute(expect_quotation(t_quot, "iflogical"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "iflogical"))


@joy_word(name="ifset", params=3, doc="X [T] [F] -> ...")
def ifset(ctx: ExecutionContext) -> None:
    """Execute T if X is set, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(x)
    if x.type == JoyType.SET:
        ctx.evaluator.execute(expect_quotation(t_quot, "ifset"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "ifset"))


@joy_word(name="ifstring", params=3, doc="X [T] [F] -> ...")
def ifstring(ctx: ExecutionContext) -> None:
    """Execute T if X is string, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(x)
    if x.type == JoyType.STRING:
        ctx.evaluator.execute(expect_quotation(t_quot, "ifstring"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "ifstring"))


@joy_word(name="iflist", params=3, doc="X [T] [F] -> ...")
def iflist(ctx: ExecutionContext) -> None:
    """Execute T if X is list, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(x)
    if x.type in (JoyType.LIST, JoyType.QUOTATION):
        ctx.evaluator.execute(expect_quotation(t_quot, "iflist"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "iflist"))


@joy_word(name="iffloat", params=3, doc="X [T] [F] -> ...")
def iffloat(ctx: ExecutionContext) -> None:
    """Execute T if X is float, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(x)
    if x.type == JoyType.FLOAT:
        ctx.evaluator.execute(expect_quotation(t_quot, "iffloat"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "iffloat"))


@joy_word(name="iffile", params=3, doc="X [T] [F] -> ...")
def iffile(ctx: ExecutionContext) -> None:
    """Execute T if X is file, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(x)
    if x.type == JoyType.FILE:
        ctx.evaluator.execute(expect_quotation(t_quot, "iffile"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "iffile"))
