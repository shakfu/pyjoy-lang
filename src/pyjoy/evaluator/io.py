"""
pyjoy.evaluator.io - Input/output primitives.

Contains: put, putch, putchars, putln, get, getch, getline, stdin, stdout,
stderr, fopen, fclose, fread, fwrite, fflush, feof, ftell, fseek, fputch,
fgetch, fputchars, fgets, ., newline
"""

from __future__ import annotations

import io as io_module
import sys

from pyjoy.errors import JoyTypeError
from pyjoy.parser import parse
from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyType, JoyValue

from .core import joy_word


def _expect_file(v: JoyValue, op: str) -> io_module.IOBase:
    """Extract file handle from JoyValue."""
    if v.type != JoyType.FILE:
        raise JoyTypeError(op, "file", v.type.name)
    if v.value is None:
        raise JoyTypeError(op, "open file", "NULL file")
    return v.value


# -----------------------------------------------------------------------------
# Output Primitives
# -----------------------------------------------------------------------------


@joy_word(name=".", params=1, doc="X ->")
def print_top(ctx: ExecutionContext) -> None:
    """Pop and print top of stack."""
    top = ctx.stack.pop()
    print(repr(top))


@joy_word(name="newline", params=0, doc="->")
def newline(ctx: ExecutionContext) -> None:
    """Print a newline."""
    print()


@joy_word(name="put", params=1, doc="X ->")
def put(ctx: ExecutionContext) -> None:
    """Write X to output, then pop X off stack."""
    x = ctx.stack.pop()
    print(repr(x), end="")


@joy_word(name=".", params=0, doc="X ->")
def dot(ctx: ExecutionContext) -> None:
    """Write X to output with newline, then pop X off stack. No-op if stack empty."""
    if ctx.stack.depth > 0:
        x = ctx.stack.pop()
        print(repr(x))


@joy_word(name="putln", params=1, doc="X ->")
def putln(ctx: ExecutionContext) -> None:
    """Write X to output with newline."""
    x = ctx.stack.pop()
    print(repr(x))


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


# -----------------------------------------------------------------------------
# Input Primitives
# -----------------------------------------------------------------------------


@joy_word(name="get", params=0, doc="-> F")
def get(ctx: ExecutionContext) -> None:
    """Read a factor from input and push it onto stack."""
    line = input()
    program = parse(line)
    for term in program.terms:
        if isinstance(term, JoyValue):
            ctx.stack.push_value(term)
        elif isinstance(term, str):
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


@joy_word(name="fopen", params=2, doc="P M -> S")
def fopen(ctx: ExecutionContext) -> None:
    """Open file with pathname P and mode M, push stream S."""
    mode, path = ctx.stack.pop_n(2)
    if path.type != JoyType.STRING:
        raise JoyTypeError("fopen", "string (path)", path.type.name)
    if mode.type != JoyType.STRING:
        raise JoyTypeError("fopen", "string (mode)", mode.type.name)

    try:
        if "b" in mode.value:
            f = open(path.value, mode.value)
        else:
            f = open(path.value, mode.value, encoding="utf-8")
        ctx.stack.push_value(JoyValue.file(f))
    except (OSError, IOError):
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

    mode = getattr(f, "mode", "")
    if isinstance(mode, str) and "b" in mode:
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
    pos = f.tell() if hasattr(f, "tell") and f.seekable() else None
    ch = f.read(1)
    at_eof = len(ch) == 0
    if pos is not None and not at_eof:
        f.seek(pos)
    ctx.stack.push_value(JoyValue.boolean(at_eof))


@joy_word(name="ferror", params=1, doc="S -> S B")
def ferror(ctx: ExecutionContext) -> None:
    """Test if stream S has an error."""
    stream = ctx.stack.peek()
    # Validate it's a file (even though we don't use the error flag)
    _expect_file(stream, "ferror")
    # Python files don't have a simple error flag like C
    # Just return false for now
    ctx.stack.push_value(JoyValue.boolean(False))


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


@joy_word(name="fputstring", params=2, doc="S T -> S")
def fputstring(ctx: ExecutionContext) -> None:
    """Write string T to stream S."""
    s, stream = ctx.stack.pop_n(2)
    f = _expect_file(stream, "fputstring")
    if s.type != JoyType.STRING:
        raise JoyTypeError("fputstring", "string", s.type.name)
    f.write(s.value)
    ctx.stack.push_value(stream)


@joy_word(name="fput", params=2, doc="S X -> S")
def fput(ctx: ExecutionContext) -> None:
    """Write value X to stream S."""
    x, stream = ctx.stack.pop_n(2)
    f = _expect_file(stream, "fput")
    f.write(repr(x))
    ctx.stack.push_value(stream)


@joy_word(name="fgets", params=1, doc="S -> S L")
def fgets(ctx: ExecutionContext) -> None:
    """Read a line from stream S."""
    stream = ctx.stack.peek()
    f = _expect_file(stream, "fgets")
    line = f.readline()
    if isinstance(line, bytes):
        line = line.decode("utf-8", errors="replace")
    ctx.stack.push_value(JoyValue.string(line))


@joy_word(name="fremove", params=1, doc="P -> B")
def fremove(ctx: ExecutionContext) -> None:
    """Remove file at path P, return success."""
    import os

    path = ctx.stack.pop()
    if path.type != JoyType.STRING:
        raise JoyTypeError("fremove", "string", path.type.name)
    try:
        os.remove(path.value)
        ctx.stack.push_value(JoyValue.boolean(True))
    except OSError:
        ctx.stack.push_value(JoyValue.boolean(False))


@joy_word(name="frename", params=2, doc="P1 P2 -> B")
def frename(ctx: ExecutionContext) -> None:
    """Rename file from P1 to P2, return success."""
    import os

    new_path, old_path = ctx.stack.pop_n(2)
    if old_path.type != JoyType.STRING:
        raise JoyTypeError("frename", "string (old)", old_path.type.name)
    if new_path.type != JoyType.STRING:
        raise JoyTypeError("frename", "string (new)", new_path.type.name)
    try:
        os.rename(old_path.value, new_path.value)
        ctx.stack.push_value(JoyValue.boolean(True))
    except OSError:
        ctx.stack.push_value(JoyValue.boolean(False))
