"""
pyjoy.evaluator.system - System operations and miscellaneous primitives.

Contains: time, clock, getenv, system, argc, argv, abort, quit, format,
formatf, strtol, strtod, intern, name, include, body, chr, ord, localtime,
gmtime, mktime, strftime, maxint, setautoput, setundeferror, gc,
autoput, undeferror, echo, conts, undefs, help, helpdetail, manual, assign
"""

from __future__ import annotations

import os
import sys
import time as time_module

from pyjoy.errors import JoyTypeError, JoyUndefinedWord
from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyQuotation, JoyType, JoyValue

from .core import joy_word


# -----------------------------------------------------------------------------
# Time Operations
# -----------------------------------------------------------------------------


@joy_word(name="time", params=0, doc="-> I")
def time_(ctx: ExecutionContext) -> None:
    """Push current time in seconds since Epoch."""
    ctx.stack.push_value(JoyValue.integer(int(time_module.time())))


@joy_word(name="clock", params=0, doc="-> I")
def clock(ctx: ExecutionContext) -> None:
    """Push CPU time in microseconds."""
    ctx.stack.push_value(JoyValue.integer(int(time_module.perf_counter() * 1_000_000)))


@joy_word(name="localtime", params=1, doc="I -> [I I I I I I B I I]")
def localtime_(ctx: ExecutionContext) -> None:
    """Convert epoch to local time [year mon day hour min sec isdst yday wday]."""
    t = ctx.stack.pop()
    if t.type != JoyType.INTEGER:
        raise JoyTypeError("localtime", "INTEGER", t.type.name)

    tm = time_module.localtime(t.value)
    result = (
        JoyValue.integer(tm.tm_year),
        JoyValue.integer(tm.tm_mon),
        JoyValue.integer(tm.tm_mday),
        JoyValue.integer(tm.tm_hour),
        JoyValue.integer(tm.tm_min),
        JoyValue.integer(tm.tm_sec),
        JoyValue.boolean(bool(tm.tm_isdst)),
        JoyValue.integer(tm.tm_yday),
        JoyValue.integer(tm.tm_wday),
    )
    ctx.stack.push_value(JoyValue.list(result))


@joy_word(name="gmtime", params=1, doc="I -> [I I I I I I B I I]")
def gmtime_(ctx: ExecutionContext) -> None:
    """Convert epoch to UTC time [year mon day hour min sec isdst yday wday]."""
    t = ctx.stack.pop()
    if t.type != JoyType.INTEGER:
        raise JoyTypeError("gmtime", "INTEGER", t.type.name)

    tm = time_module.gmtime(t.value)
    result = (
        JoyValue.integer(tm.tm_year),
        JoyValue.integer(tm.tm_mon),
        JoyValue.integer(tm.tm_mday),
        JoyValue.integer(tm.tm_hour),
        JoyValue.integer(tm.tm_min),
        JoyValue.integer(tm.tm_sec),
        JoyValue.boolean(bool(tm.tm_isdst)),
        JoyValue.integer(tm.tm_yday),
        JoyValue.integer(tm.tm_wday),
    )
    ctx.stack.push_value(JoyValue.list(result))


@joy_word(name="mktime", params=1, doc="[I I I I I I B I I] -> I")
def mktime_(ctx: ExecutionContext) -> None:
    """Convert time list to epoch."""
    lst = ctx.stack.pop()
    if lst.type not in (JoyType.LIST, JoyType.QUOTATION):
        raise JoyTypeError("mktime", "LIST", lst.type.name)

    items = lst.value if lst.type == JoyType.LIST else lst.value.terms
    if len(items) < 9:
        raise JoyTypeError("mktime", "list of 9 integers", f"list of {len(items)}")

    try:
        tm_tuple = (
            int(items[0].value),  # year
            int(items[1].value),  # month
            int(items[2].value),  # day
            int(items[3].value),  # hour
            int(items[4].value),  # min
            int(items[5].value),  # sec
            int(items[8].value),  # wday
            int(items[7].value),  # yday
            int(items[6].value) if items[6].type == JoyType.INTEGER else (1 if items[6].value else 0),  # isdst
        )
        result = int(time_module.mktime(tm_tuple))
        ctx.stack.push_value(JoyValue.integer(result))
    except (ValueError, OverflowError):
        ctx.stack.push_value(JoyValue.integer(-1))


@joy_word(name="strftime", params=2, doc="[T] S -> S")
def strftime_(ctx: ExecutionContext) -> None:
    """Format time list with format string."""
    fmt, lst = ctx.stack.pop_n(2)
    if fmt.type != JoyType.STRING:
        raise JoyTypeError("strftime", "STRING", fmt.type.name)
    if lst.type not in (JoyType.LIST, JoyType.QUOTATION):
        raise JoyTypeError("strftime", "LIST", lst.type.name)

    items = lst.value if lst.type == JoyType.LIST else lst.value.terms
    if len(items) < 9:
        ctx.stack.push_value(JoyValue.string(""))
        return

    try:
        tm_tuple = (
            int(items[0].value),
            int(items[1].value),
            int(items[2].value),
            int(items[3].value),
            int(items[4].value),
            int(items[5].value),
            int(items[8].value),
            int(items[7].value),
            int(items[6].value) if items[6].type == JoyType.INTEGER else (1 if items[6].value else 0),
        )
        result = time_module.strftime(fmt.value, tm_tuple)
        ctx.stack.push_value(JoyValue.string(result))
    except (ValueError, OverflowError):
        ctx.stack.push_value(JoyValue.string(""))


# -----------------------------------------------------------------------------
# Environment Operations
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# Program Control
# -----------------------------------------------------------------------------


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


@joy_word(name="gc", params=0, doc="->")
def gc_(ctx: ExecutionContext) -> None:
    """Trigger garbage collection (no-op in Python)."""
    import gc
    gc.collect()


# -----------------------------------------------------------------------------
# Formatting
# -----------------------------------------------------------------------------


@joy_word(name="format", params=4, doc="N C I J -> S")
def format_(ctx: ExecutionContext) -> None:
    """Format N in mode C with max width I and min width J."""
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
        result = f"{int(n.value):*>{width}.{prec}d}" if prec else f"{int(n.value):>{width}d}"
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


@joy_word(name="formatf", params=4, doc="F C I J -> S")
def formatf(ctx: ExecutionContext) -> None:
    """Format float F with char C, width I, precision J."""
    j, i, c, f = ctx.stack.pop_n(4)
    if f.type not in (JoyType.FLOAT, JoyType.INTEGER):
        raise JoyTypeError("formatf", "numeric", f.type.name)
    if c.type != JoyType.CHAR:
        raise JoyTypeError("formatf", "char", c.type.name)

    width = int(i.value) if i.type == JoyType.INTEGER else 0
    precision = int(j.value) if j.type == JoyType.INTEGER else 6
    spec = c.value

    fmt = f"%{width}.{precision}{spec}"
    try:
        result = fmt % float(f.value)
    except (ValueError, TypeError):
        result = str(f.value)

    ctx.stack.push_value(JoyValue.string(result))


# -----------------------------------------------------------------------------
# String Conversions
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


# -----------------------------------------------------------------------------
# Character Operations
# -----------------------------------------------------------------------------


@joy_word(name="chr", params=1, doc="I -> C")
def chr_(ctx: ExecutionContext) -> None:
    """Convert integer to character."""
    n = ctx.stack.pop()
    if n.type != JoyType.INTEGER:
        raise JoyTypeError("chr", "INTEGER", n.type.name)
    ctx.stack.push_value(JoyValue.char(chr(n.value)))


@joy_word(name="ord", params=1, doc="C -> I")
def ord_(ctx: ExecutionContext) -> None:
    """Convert character to integer."""
    c = ctx.stack.pop()
    if c.type == JoyType.CHAR:
        ctx.stack.push_value(JoyValue.integer(ord(c.value)))
    elif c.type == JoyType.STRING and len(c.value) > 0:
        ctx.stack.push_value(JoyValue.integer(ord(c.value[0])))
    elif c.type == JoyType.INTEGER:
        ctx.stack.push_value(c)  # Already an integer
    else:
        raise JoyTypeError("ord", "CHAR or STRING", c.type.name)


# -----------------------------------------------------------------------------
# Include and Definitions
# -----------------------------------------------------------------------------


@joy_word(name="include", params=1, doc="S ->")
def include_(ctx: ExecutionContext) -> None:
    """Load and execute a Joy file."""
    filename = ctx.stack.pop()
    if filename.type != JoyType.STRING:
        raise JoyTypeError("include", "STRING", filename.type.name)

    path = filename.value

    search_paths = [
        os.path.dirname(os.path.abspath(path)),
        os.getcwd(),
    ]

    stdlib_path = os.path.join(os.path.dirname(__file__), "..", "stdlib")
    if os.path.exists(stdlib_path):
        search_paths.append(stdlib_path)

    file_path = None
    if os.path.isabs(path):
        if os.path.exists(path):
            file_path = path
    else:
        for search_dir in search_paths:
            candidate = os.path.join(search_dir, path)
            if os.path.exists(candidate):
                file_path = candidate
                break
        if file_path is None and os.path.exists(path):
            file_path = path

    if file_path is None:
        raise JoyUndefinedWord(f"include: file not found: {path}")

    with open(file_path, "r") as f:
        source = f.read()

    from pyjoy.parser import Parser

    parser = Parser()
    result = parser.parse_full(source)

    for defn in result.definitions:
        ctx.evaluator.define(defn.name, defn.body)

    ctx.evaluator.execute(result.program)


@joy_word(name="body", params=1, doc="U -> [P]")
def body_(ctx: ExecutionContext) -> None:
    """Get the body of a user-defined word (or [] if undefined/primitive)."""
    u = ctx.stack.pop()
    if u.type == JoyType.SYMBOL:
        name = u.value
    elif u.type == JoyType.STRING:
        name = u.value
    else:
        ctx.stack.push_value(JoyValue.quotation(JoyQuotation(())))
        return

    if name in ctx.evaluator.definitions:
        ctx.stack.push_value(JoyValue.quotation(ctx.evaluator.definitions[name]))
    else:
        ctx.stack.push_value(JoyValue.quotation(JoyQuotation(())))


@joy_word(name="assign", params=2, doc="X N ->")
def assign_(ctx: ExecutionContext) -> None:
    """Assign value X to symbol N (define)."""
    name_val, value = ctx.stack.pop_n(2)
    if name_val.type == JoyType.SYMBOL:
        name = name_val.value
    elif name_val.type == JoyType.STRING:
        name = name_val.value
    else:
        raise JoyTypeError("assign", "symbol or string", name_val.type.name)

    # Create a quotation that just pushes the value
    ctx.evaluator.define(name, JoyQuotation((value,)))


# -----------------------------------------------------------------------------
# Interpreter State
# -----------------------------------------------------------------------------


@joy_word(name="maxint", params=0, doc="-> I")
def maxint_(ctx: ExecutionContext) -> None:
    """Push maximum integer value."""
    ctx.stack.push_value(JoyValue.integer(sys.maxsize))


@joy_word(name="setautoput", params=1, doc="I ->")
def setautoput_(ctx: ExecutionContext) -> None:
    """Set autoput mode (stub)."""
    ctx.stack.pop()


@joy_word(name="setundeferror", params=1, doc="I ->")
def setundeferror_(ctx: ExecutionContext) -> None:
    """Set undefined error mode (stub)."""
    ctx.stack.pop()


@joy_word(name="autoput", params=0, doc="-> I")
def autoput_(ctx: ExecutionContext) -> None:
    """Get autoput mode (stub, returns 0)."""
    ctx.stack.push_value(JoyValue.integer(0))


@joy_word(name="undeferror", params=0, doc="-> I")
def undeferror_(ctx: ExecutionContext) -> None:
    """Get undefined error mode (stub, returns 0)."""
    ctx.stack.push_value(JoyValue.integer(0))


@joy_word(name="echo", params=0, doc="-> I")
def echo_(ctx: ExecutionContext) -> None:
    """Get echo mode (stub, returns 0)."""
    ctx.stack.push_value(JoyValue.integer(0))


@joy_word(name="conts", params=0, doc="-> L")
def conts_(ctx: ExecutionContext) -> None:
    """Push current continuations (stub, returns empty list)."""
    ctx.stack.push_value(JoyValue.list(()))


@joy_word(name="undefs", params=0, doc="-> L")
def undefs_(ctx: ExecutionContext) -> None:
    """Push list of undefined words encountered (stub)."""
    ctx.stack.push_value(JoyValue.list(()))


@joy_word(name="__settracegc", params=1, doc="I ->")
def settracegc_(ctx: ExecutionContext) -> None:
    """Debug no-op."""
    ctx.stack.pop()


# -----------------------------------------------------------------------------
# Help Commands
# -----------------------------------------------------------------------------


@joy_word(name="help", params=0, doc="->")
def help_(ctx: ExecutionContext) -> None:
    """List all defined symbols and primitives."""
    from .core import list_primitives

    if ctx.evaluator.definitions:
        print("User definitions:")
        for name in sorted(ctx.evaluator.definitions.keys()):
            print(f"  {name}")
        print()

    print("Primitives:")
    for name in list_primitives():
        print(f"  {name}")


@joy_word(name="helpdetail", params=1, doc="[S1 S2 ..] ->")
def helpdetail_(ctx: ExecutionContext) -> None:
    """Give brief help on each symbol in the list."""
    from .core import get_primitive

    symbols = ctx.stack.pop()
    if symbols.type not in (JoyType.LIST, JoyType.QUOTATION):
        raise JoyTypeError("helpdetail", "LIST or QUOTATION", symbols.type.name)

    items = symbols.value if symbols.type == JoyType.LIST else symbols.value.terms

    for item in items:
        if isinstance(item, JoyValue):
            if item.type == JoyType.SYMBOL:
                name = item.value
            elif item.type == JoyType.STRING:
                name = item.value
            else:
                continue
        elif isinstance(item, str):
            name = item
        else:
            continue

        prim = get_primitive(name)
        if prim is not None:
            doc = getattr(prim, "joy_doc", "") or ""
            print(f"{name} : {doc}")
        elif name in ctx.evaluator.definitions:
            print(f"{name} : (user-defined)")
        else:
            print(f"{name} : (undefined)")


@joy_word(name="manual", params=0, doc="->")
def manual_(ctx: ExecutionContext) -> None:
    """Print the manual of all Joy primitives."""
    from .core import list_primitives, get_primitive

    print("Joy Primitives Manual")
    print("=" * 60)
    print()

    for name in list_primitives():
        prim = get_primitive(name)
        if prim is not None:
            doc = getattr(prim, "joy_doc", "") or ""
            desc = prim.__doc__ or ""
            print(f"{name} : {doc}")
            if desc:
                print(f"    {desc.split(chr(10))[0]}")
            print()
