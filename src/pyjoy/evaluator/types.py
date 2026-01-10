"""
pyjoy.evaluator.types - Type predicates and conditionals.

Contains type predicates: integer, float, char, string, list, logical, set,
leaf, file, user, sametype, typeof

Contains type conditionals: ifinteger, ifchar, iflogical, ifset, ifstring,
iflist, iffloat, iffile
"""

from __future__ import annotations

from typing import Any

from pyjoy.errors import JoyTypeError
from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyQuotation, JoyType, JoyValue

from .core import expect_quotation, get_primitive, is_joy_value, joy_word


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

# -----------------------------------------------------------------------------
# Type Predicates
# -----------------------------------------------------------------------------


def _check_type(x: Any, joy_type: JoyType, python_types: tuple) -> bool:
    """Check if x matches the given Joy type or Python types."""
    if is_joy_value(x):
        return x.type == joy_type
    return isinstance(x, python_types)


@joy_word(name="integer", params=1, doc="X -> B")
def is_integer(ctx: ExecutionContext) -> None:
    """Test if X is an integer."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        result = x.type == JoyType.INTEGER
    else:
        result = isinstance(x, int) and not isinstance(x, bool)
    _push_boolean(ctx, result)


@joy_word(name="float", params=1, doc="X -> B")
def is_float(ctx: ExecutionContext) -> None:
    """Test if X is a float."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        result = x.type == JoyType.FLOAT
    else:
        result = isinstance(x, float)
    _push_boolean(ctx, result)


@joy_word(name="char", params=1, doc="X -> B")
def is_char(ctx: ExecutionContext) -> None:
    """Test if X is a character."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        result = x.type == JoyType.CHAR
    else:
        # In pythonic mode, a single-character string is a char
        result = isinstance(x, str) and len(x) == 1
    _push_boolean(ctx, result)


@joy_word(name="string", params=1, doc="X -> B")
def is_string(ctx: ExecutionContext) -> None:
    """Test if X is a string."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        result = x.type == JoyType.STRING
    else:
        # In pythonic mode, multi-char strings are strings (not chars)
        result = isinstance(x, str) and len(x) != 1
    _push_boolean(ctx, result)


@joy_word(name="list", params=1, doc="X -> B")
def is_list(ctx: ExecutionContext) -> None:
    """Test if X is a list (or quotation, treated as list in Joy)."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        result = x.type in (JoyType.LIST, JoyType.QUOTATION)
    else:
        result = isinstance(x, (list, tuple, JoyQuotation))
    _push_boolean(ctx, result)


@joy_word(name="logical", params=1, doc="X -> B")
def is_logical(ctx: ExecutionContext) -> None:
    """Test if X is a boolean."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        result = x.type == JoyType.BOOLEAN
    else:
        result = isinstance(x, bool)
    _push_boolean(ctx, result)


@joy_word(name="set", params=1, doc="X -> B")
def is_set(ctx: ExecutionContext) -> None:
    """Test if X is a set."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        result = x.type == JoyType.SET
    else:
        result = isinstance(x, frozenset)
    _push_boolean(ctx, result)


@joy_word(name="leaf", params=1, doc="X -> B")
def is_leaf(ctx: ExecutionContext) -> None:
    """Test if X is an atom (not a list or quotation)."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        is_aggregate = x.type in (JoyType.LIST, JoyType.QUOTATION)
    else:
        is_aggregate = isinstance(x, (list, tuple, JoyQuotation))
    _push_boolean(ctx, not is_aggregate)


@joy_word(name="file", params=1, doc="X -> B")
def is_file(ctx: ExecutionContext) -> None:
    """Test if X is a file handle."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        result = x.type == JoyType.FILE
    else:
        # In pythonic mode, check for file-like object
        result = hasattr(x, 'read') and hasattr(x, 'write')
    _push_boolean(ctx, result)


@joy_word(name="user", params=1, doc="X -> B")
def is_user(ctx: ExecutionContext) -> None:
    """Test if X is a user-defined symbol."""
    x = ctx.stack.pop()
    if is_joy_value(x):
        if x.type != JoyType.SYMBOL:
            _push_boolean(ctx, False)
        else:
            is_defined = x.value in ctx.evaluator.definitions
            _push_boolean(ctx, is_defined)
    else:
        # In pythonic mode, symbols are just strings
        if isinstance(x, str):
            is_defined = x in ctx.evaluator.definitions
            _push_boolean(ctx, is_defined)
        else:
            _push_boolean(ctx, False)


def _get_type_key(x: Any) -> str:
    """Get a type key for comparison purposes."""
    if is_joy_value(x):
        return x.type.name
    if isinstance(x, bool):
        return "BOOLEAN"
    if isinstance(x, int):
        return "INTEGER"
    if isinstance(x, float):
        return "FLOAT"
    if isinstance(x, str):
        if len(x) == 1:
            return "CHAR"
        return "STRING"
    if isinstance(x, (list, tuple)):
        return "LIST"
    if isinstance(x, JoyQuotation):
        return "QUOTATION"
    if isinstance(x, frozenset):
        return "SET"
    return "OBJECT"


@joy_word(name="sametype", params=2, doc="X Y -> B")
def sametype(ctx: ExecutionContext) -> None:
    """Test if X and Y have the same type.

    For symbols, Joy42 semantics are:
    - Two builtins are sametype only if they're the same builtin (same name)
    - Two user-defined words are sametype (regardless of which word)
    - A builtin and user-defined word are not sametype
    """
    b, a = ctx.stack.pop_n(2)

    if is_joy_value(a) and is_joy_value(b):
        # Both are JoyValues - check types
        if a.type != b.type:
            result = False
        elif a.type == JoyType.SYMBOL:
            # For symbols, check if both are same kind (builtin or user-defined)
            # and for builtins, must be the same symbol
            a_is_builtin = get_primitive(a.value) is not None
            b_is_builtin = get_primitive(b.value) is not None
            a_is_usrdef = a.value in ctx.evaluator.definitions
            b_is_usrdef = b.value in ctx.evaluator.definitions

            if a_is_builtin and b_is_builtin:
                # Two builtins - must be same symbol
                result = a.value == b.value
            elif a_is_usrdef and b_is_usrdef:
                # Two user-defined - always sametype
                result = True
            elif not a_is_builtin and not a_is_usrdef and not b_is_builtin and not b_is_usrdef:
                # Both are unknown symbols - same unknown type
                result = True
            else:
                # Mix of builtin/usrdef/unknown - different types
                result = False
        else:
            # Non-symbol types - same type is sufficient
            result = True
    else:
        result = _get_type_key(a) == _get_type_key(b)

    _push_boolean(ctx, result)


@joy_word(name="typeof", params=1, doc="X -> I")
def typeof_(ctx: ExecutionContext) -> None:
    """Return type of X as integer.

    Joy42 type codes:
    0 = UNKNOWN, 1 = (reserved), 2 = USRDEF, 3 = BUILTIN,
    4 = BOOLEAN, 5 = CHAR, 6 = INTEGER, 7 = SET,
    8 = STRING, 9 = LIST, 10 = FLOAT, 11 = FILE
    """
    x = ctx.stack.pop()

    # Handle JoyValue objects
    if is_joy_value(x):
        # For symbols, check if it's a builtin or user-defined
        if x.type == JoyType.SYMBOL:
            # Check if it's registered as a primitive
            is_primitive = get_primitive(x.value) is not None
            is_user_def = x.value in ctx.evaluator.definitions
            if is_primitive and not is_user_def:
                _push_integer(ctx, 3)  # BUILTIN
            else:
                _push_integer(ctx, 2)  # USRDEF
            return

        type_codes = {
            JoyType.BOOLEAN: 4,
            JoyType.CHAR: 5,
            JoyType.INTEGER: 6,
            JoyType.SET: 7,
            JoyType.STRING: 8,
            JoyType.LIST: 9,
            JoyType.QUOTATION: 9,  # Quotation treated as list
            JoyType.FLOAT: 10,
            JoyType.FILE: 11,
        }
        _push_integer(ctx, type_codes.get(x.type, 0))
        return

    # Handle raw Python values (pythonic mode)
    if isinstance(x, bool):
        _push_integer(ctx, 4)  # BOOLEAN
    elif isinstance(x, int):
        _push_integer(ctx, 6)  # INTEGER
    elif isinstance(x, float):
        _push_integer(ctx, 10)  # FLOAT
    elif isinstance(x, str):
        if len(x) == 1:
            _push_integer(ctx, 5)  # CHAR
        else:
            _push_integer(ctx, 8)  # STRING
    elif isinstance(x, (list, tuple, JoyQuotation)):
        _push_integer(ctx, 9)  # LIST
    elif isinstance(x, frozenset):
        _push_integer(ctx, 7)  # SET
    elif hasattr(x, 'read') and hasattr(x, 'write'):
        _push_integer(ctx, 11)  # FILE
    else:
        _push_integer(ctx, 0)  # UNKNOWN


def _get_int_value(v: Any, op: str) -> int:
    """Extract integer value from JoyValue or raw int."""
    if is_joy_value(v):
        if v.type != JoyType.INTEGER:
            raise JoyTypeError(op, "INTEGER", v.type.name)
        return v.value
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    raise JoyTypeError(op, "INTEGER", type(v).__name__)


def _is_truthy(v: Any) -> bool:
    """Check if a value is truthy (mode-aware)."""
    if is_joy_value(v):
        return v.is_truthy()
    return bool(v)


@joy_word(name="casting", params=2, doc="X T -> Y")
def casting_(ctx: ExecutionContext) -> None:
    """Cast value X to type T (type code from typeof).

    Joy42 type codes (matching typeof):
    4 = BOOLEAN, 5 = CHAR, 6 = INTEGER, 7 = SET,
    8 = STRING, 9 = LIST, 10 = FLOAT, 11 = FILE
    """
    t, x = ctx.stack.pop_n(2)
    target_type = _get_int_value(t, "casting")

    # Helper to push result in mode-appropriate way
    def push_result(value: Any) -> None:
        if ctx.strict:
            ctx.stack.push_value(value)
        else:
            ctx.stack.push(value)

    # Get raw value and type info for x
    if is_joy_value(x):
        x_type = x.type
        x_val = x.value
    else:
        x_val = x
        # Infer type from Python value
        if isinstance(x, bool):
            x_type = JoyType.BOOLEAN
        elif isinstance(x, int):
            x_type = JoyType.INTEGER
        elif isinstance(x, float):
            x_type = JoyType.FLOAT
        elif isinstance(x, str):
            x_type = JoyType.CHAR if len(x) == 1 else JoyType.STRING
        elif isinstance(x, (list, tuple)):
            x_type = JoyType.LIST
        elif isinstance(x, JoyQuotation):
            x_type = JoyType.QUOTATION
        elif isinstance(x, frozenset):
            x_type = JoyType.SET
        else:
            x_type = JoyType.OBJECT

    # Joy42 type codes: 4=bool, 5=char, 6=int, 7=set, 8=string, 9=list, 10=float, 11=file
    if target_type == 4:  # BOOLEAN
        result = _is_truthy(x)
        push_result(JoyValue.boolean(result) if ctx.strict else result)

    elif target_type == 5:  # CHAR
        if x_type == JoyType.CHAR:
            push_result(x)
        elif x_type == JoyType.INTEGER:
            ch = chr(x_val & 0xFF)  # type: ignore[operator]
            push_result(JoyValue.char(ch) if ctx.strict else ch)
        elif x_type == JoyType.STRING and x_val:
            ch = x_val[0]  # type: ignore[index]
            push_result(JoyValue.char(ch) if ctx.strict else ch)
        else:
            push_result(JoyValue.char("\0") if ctx.strict else "\0")

    elif target_type == 6:  # INTEGER
        if x_type == JoyType.INTEGER:
            push_result(x)
        elif x_type == JoyType.CHAR:
            val = ord(x_val)  # type: ignore[arg-type]
            push_result(JoyValue.integer(val) if ctx.strict else val)
        elif x_type == JoyType.FLOAT:
            val = int(x_val)  # type: ignore[arg-type]
            push_result(JoyValue.integer(val) if ctx.strict else val)
        elif x_type == JoyType.BOOLEAN:
            val = 1 if x_val else 0
            push_result(JoyValue.integer(val) if ctx.strict else val)
        elif x_type == JoyType.SET:
            # Convert set to bitfield integer
            int_val = 0
            for bit in x_val:  # type: ignore[union-attr]
                int_val |= 1 << bit
            push_result(JoyValue.integer(int_val) if ctx.strict else int_val)
        else:
            push_result(JoyValue.integer(0) if ctx.strict else 0)

    elif target_type == 7:  # SET
        if x_type == JoyType.SET:
            push_result(x)
        elif x_type == JoyType.INTEGER:
            # Convert int bits to set members
            bits: set[int] = set()
            int_val: int = x_val  # type: ignore[assignment]
            for i in range(64):
                if int_val & (1 << i):
                    bits.add(i)
            result_set: frozenset[int] = frozenset(bits)
            push_result(JoyValue.joy_set(result_set) if ctx.strict else result_set)
        elif x_type == JoyType.LIST:
            if is_joy_value(x):
                items = frozenset(
                    v.value
                    for v in x_val  # type: ignore[union-attr]
                    if is_joy_value(v) and v.type == JoyType.INTEGER
                )
            else:
                items = frozenset(
                    v for v in x_val  # type: ignore[union-attr]
                    if isinstance(v, int) and not isinstance(v, bool)
                )
            push_result(JoyValue.joy_set(items) if ctx.strict else items)
        else:
            push_result(JoyValue.joy_set(frozenset()) if ctx.strict else frozenset())

    elif target_type == 8:  # STRING
        if x_type == JoyType.STRING:
            push_result(x)
        elif x_type == JoyType.CHAR:
            push_result(JoyValue.string(x_val) if ctx.strict else x_val)  # type: ignore[arg-type]
        elif x_type == JoyType.INTEGER:
            s = str(x_val)
            push_result(JoyValue.string(s) if ctx.strict else s)
        elif x_type == JoyType.FLOAT:
            s = str(x_val)
            push_result(JoyValue.string(s) if ctx.strict else s)
        elif x_type == JoyType.LIST:
            if is_joy_value(x):
                chars = "".join(
                    v.value
                    for v in x_val  # type: ignore[union-attr]
                    if is_joy_value(v) and v.type == JoyType.CHAR
                )
            else:
                chars = "".join(
                    str(v) for v in x_val  # type: ignore[union-attr]
                    if isinstance(v, str) and len(v) == 1
                )
            push_result(JoyValue.string(chars) if ctx.strict else chars)
        else:
            s = str(x_val)
            push_result(JoyValue.string(s) if ctx.strict else s)

    elif target_type == 9:  # LIST
        if x_type in (JoyType.LIST, JoyType.QUOTATION):
            push_result(x)
        elif x_type == JoyType.STRING:
            if ctx.strict:
                chars = tuple(JoyValue.char(c) for c in x_val)  # type: ignore[union-attr]
                push_result(JoyValue.list(chars))
            else:
                push_result(list(x_val))  # type: ignore[arg-type]
        elif x_type == JoyType.SET:
            if ctx.strict:
                items = tuple(JoyValue.integer(i) for i in sorted(x_val))  # type: ignore[arg-type]
                push_result(JoyValue.list(items))
            else:
                push_result(list(sorted(x_val)))  # type: ignore[arg-type]
        else:
            push_result(JoyValue.list(()) if ctx.strict else [])

    elif target_type == 10:  # FLOAT
        if x_type == JoyType.FLOAT:
            push_result(x)
        elif x_type == JoyType.INTEGER:
            # Bit-level reinterpretation: treat integer bits as IEEE 754 double
            import struct

            int_val: int = x_val & 0xFFFFFFFFFFFFFFFF  # type: ignore[assignment]
            val = struct.unpack("d", struct.pack("Q", int_val))[0]
            push_result(JoyValue.floating(val) if ctx.strict else val)
        elif x_type == JoyType.CHAR:
            val = float(ord(x_val))  # type: ignore[arg-type]
            push_result(JoyValue.floating(val) if ctx.strict else val)
        elif x_type == JoyType.BOOLEAN:
            val = 1.0 if x_val else 0.0
            push_result(JoyValue.floating(val) if ctx.strict else val)
        else:
            push_result(JoyValue.floating(0.0) if ctx.strict else 0.0)

    elif target_type == 11:  # FILE
        # Can't really cast to file
        push_result(JoyValue.file(None) if ctx.strict else None)

    else:
        # Unknown type code - return value unchanged
        push_result(x)


# Bit-level reinterpretation casting
@joy_word(name="bitcast", params=2, doc="X T -> Y")
def bitcast_(ctx: ExecutionContext) -> None:
    """Bit-level reinterpretation cast (for low-level operations).

    Type codes: 0=int-to-float-bits, 1=float-to-int-bits
    """
    import struct

    t, x = ctx.stack.pop_n(2)
    target_type = _get_int_value(t, "bitcast")

    if is_joy_value(x):
        x_val = x.value
    else:
        x_val = x

    def push_result(value: Any) -> None:
        if ctx.strict:
            ctx.stack.push_value(value)
        else:
            ctx.stack.push(value)

    if target_type == 0:  # int bits -> float
        try:
            result = struct.unpack("d", struct.pack("q", x_val))[0]
            push_result(JoyValue.floating(result) if ctx.strict else result)
        except struct.error:
            push_result(JoyValue.floating(0.0) if ctx.strict else 0.0)

    elif target_type == 1:  # float bits -> int
        try:
            result = struct.unpack("q", struct.pack("d", x_val))[0]
            push_result(JoyValue.integer(result) if ctx.strict else result)
        except struct.error:
            push_result(JoyValue.integer(0) if ctx.strict else 0)

    else:
        # Unknown type, return as-is
        push_result(x)


# -----------------------------------------------------------------------------
# Type Conditionals
# -----------------------------------------------------------------------------


def _check_is_integer(x: Any) -> bool:
    """Check if x is an integer (mode-aware)."""
    if is_joy_value(x):
        return x.type == JoyType.INTEGER
    return isinstance(x, int) and not isinstance(x, bool)


def _check_is_char(x: Any) -> bool:
    """Check if x is a character (mode-aware)."""
    if is_joy_value(x):
        return x.type == JoyType.CHAR
    return isinstance(x, str) and len(x) == 1


def _check_is_logical(x: Any) -> bool:
    """Check if x is a boolean (mode-aware)."""
    if is_joy_value(x):
        return x.type == JoyType.BOOLEAN
    return isinstance(x, bool)


def _check_is_set(x: Any) -> bool:
    """Check if x is a set (mode-aware)."""
    if is_joy_value(x):
        return x.type == JoyType.SET
    return isinstance(x, frozenset)


def _check_is_string(x: Any) -> bool:
    """Check if x is a string (mode-aware)."""
    if is_joy_value(x):
        return x.type == JoyType.STRING
    # In pythonic mode, multi-char strings are strings (not chars)
    return isinstance(x, str) and len(x) != 1


def _check_is_list(x: Any) -> bool:
    """Check if x is a list or quotation (mode-aware)."""
    if is_joy_value(x):
        return x.type in (JoyType.LIST, JoyType.QUOTATION)
    return isinstance(x, (list, tuple, JoyQuotation))


def _check_is_float(x: Any) -> bool:
    """Check if x is a float (mode-aware)."""
    if is_joy_value(x):
        return x.type == JoyType.FLOAT
    return isinstance(x, float)


def _check_is_file(x: Any) -> bool:
    """Check if x is a file (mode-aware)."""
    if is_joy_value(x):
        return x.type == JoyType.FILE
    return hasattr(x, 'read') and hasattr(x, 'write')


def _push_value_for_conditional(ctx: ExecutionContext, x: Any) -> None:
    """Push x back to stack in mode-appropriate way."""
    if ctx.strict:
        ctx.stack.push_value(x)
    else:
        ctx.stack.push(x)


@joy_word(name="ifinteger", params=3, doc="X [T] [F] -> ...")
def ifinteger(ctx: ExecutionContext) -> None:
    """Execute T if X is integer, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    _push_value_for_conditional(ctx, x)
    if _check_is_integer(x):
        ctx.evaluator.execute(expect_quotation(t_quot, "ifinteger"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "ifinteger"))


@joy_word(name="ifchar", params=3, doc="X [T] [F] -> ...")
def ifchar(ctx: ExecutionContext) -> None:
    """Execute T if X is char, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    _push_value_for_conditional(ctx, x)
    if _check_is_char(x):
        ctx.evaluator.execute(expect_quotation(t_quot, "ifchar"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "ifchar"))


@joy_word(name="iflogical", params=3, doc="X [T] [F] -> ...")
def iflogical(ctx: ExecutionContext) -> None:
    """Execute T if X is boolean, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    _push_value_for_conditional(ctx, x)
    if _check_is_logical(x):
        ctx.evaluator.execute(expect_quotation(t_quot, "iflogical"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "iflogical"))


@joy_word(name="ifset", params=3, doc="X [T] [F] -> ...")
def ifset(ctx: ExecutionContext) -> None:
    """Execute T if X is set, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    _push_value_for_conditional(ctx, x)
    if _check_is_set(x):
        ctx.evaluator.execute(expect_quotation(t_quot, "ifset"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "ifset"))


@joy_word(name="ifstring", params=3, doc="X [T] [F] -> ...")
def ifstring(ctx: ExecutionContext) -> None:
    """Execute T if X is string, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    _push_value_for_conditional(ctx, x)
    if _check_is_string(x):
        ctx.evaluator.execute(expect_quotation(t_quot, "ifstring"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "ifstring"))


@joy_word(name="iflist", params=3, doc="X [T] [F] -> ...")
def iflist(ctx: ExecutionContext) -> None:
    """Execute T if X is list, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    _push_value_for_conditional(ctx, x)
    if _check_is_list(x):
        ctx.evaluator.execute(expect_quotation(t_quot, "iflist"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "iflist"))


@joy_word(name="iffloat", params=3, doc="X [T] [F] -> ...")
def iffloat(ctx: ExecutionContext) -> None:
    """Execute T if X is float, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    _push_value_for_conditional(ctx, x)
    if _check_is_float(x):
        ctx.evaluator.execute(expect_quotation(t_quot, "iffloat"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "iffloat"))


@joy_word(name="iffile", params=3, doc="X [T] [F] -> ...")
def iffile(ctx: ExecutionContext) -> None:
    """Execute T if X is file, else F."""
    f_quot, t_quot, x = ctx.stack.pop_n(3)
    _push_value_for_conditional(ctx, x)
    if _check_is_file(x):
        ctx.evaluator.execute(expect_quotation(t_quot, "iffile"))
    else:
        ctx.evaluator.execute(expect_quotation(f_quot, "iffile"))
