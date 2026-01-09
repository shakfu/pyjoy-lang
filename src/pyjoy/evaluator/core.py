"""
pyjoy.evaluator.core - Core evaluator infrastructure.

Contains:
- joy_word decorator for defining primitives (full stack control)
- python_word decorator for simple auto-pop/push primitives
- Evaluator class for executing Joy programs
- Primitive registry functions
- Mode-aware value extraction helpers

Decorator Comparison:

    @joy_word(name="+", params=2, doc="N1 N2 -> N3")
    def plus(ctx: ExecutionContext):
        b, a = ctx.stack.pop_n(2)
        ctx.stack.push_value(JoyValue.integer(a.value + b.value))

    @python_word(name="+", doc="N1 N2 -> N3")
    def plus(a, b):
        return a + b

Use @joy_word when you need:
  - Direct stack access (e.g., for combinators)
  - Multiple results pushed to stack
  - Complex control flow
  - Access to ExecutionContext for mode checking

Use @python_word when you have:
  - Pure functions with fixed arity
  - Single return value (or None)
  - Simple value transformations
"""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union

from pyjoy.errors import JoyStackUnderflow, JoyTypeError, JoyUndefinedWord
from pyjoy.parser import Definition, Parser, PythonExpr, PythonStmt
from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyQuotation, JoyType, JoyValue, python_to_joy


class PythonInteropError(Exception):
    """Raised when Python interop is used in strict mode."""

    pass

# Type alias for Joy word implementations
WordFunc = Callable[[ExecutionContext], None]

# Global registry for primitive words
_primitives: Dict[str, WordFunc] = {}


# -----------------------------------------------------------------------------
# Mode-Aware Value Helpers
# -----------------------------------------------------------------------------


def unwrap_value(value: Any) -> Any:
    """
    Extract raw Python value from JoyValue or return as-is.

    Works in both strict and pythonic modes:
    - If value is JoyValue, returns value.value
    - Otherwise returns value unchanged

    Args:
        value: JoyValue or raw Python value

    Returns:
        Raw Python value
    """
    if isinstance(value, JoyValue):
        return value.value
    return value


def wrap_value(value: Any, strict: bool = True) -> Any:
    """
    Wrap value appropriately based on mode.

    Args:
        value: Raw Python value to wrap
        strict: If True, wrap in JoyValue; if False, return as-is

    Returns:
        JoyValue in strict mode, raw value in pythonic mode
    """
    if strict:
        return python_to_joy(value, strict=True)
    return value


def is_joy_value(value: Any) -> bool:
    """Check if value is a JoyValue instance."""
    return isinstance(value, JoyValue)


def get_numeric(value: Any) -> Union[int, float]:
    """
    Extract numeric value from JoyValue or raw Python value.

    Handles both strict mode (JoyValue) and pythonic mode (raw values).

    Args:
        value: JoyValue or raw numeric value

    Returns:
        int or float

    Raises:
        JoyTypeError: If value is not numeric
    """
    if isinstance(value, JoyValue):
        if value.type == JoyType.INTEGER:
            return value.value
        elif value.type == JoyType.FLOAT:
            return value.value
        elif value.type == JoyType.CHAR:
            return ord(value.value)
        elif value.type == JoyType.BOOLEAN:
            return 1 if value.value else 0
        else:
            raise JoyTypeError("arithmetic", "numeric", value.type.name)
    elif isinstance(value, bool):
        return 1 if value else 0
    elif isinstance(value, (int, float)):
        return value
    elif isinstance(value, str) and len(value) == 1:
        return ord(value)
    else:
        raise JoyTypeError("arithmetic", "numeric", type(value).__name__)


def make_numeric_result(value: Union[int, float], strict: bool = True) -> Any:
    """
    Create appropriate numeric result based on mode.

    Args:
        value: Numeric result
        strict: If True, wrap in JoyValue

    Returns:
        JoyValue in strict mode, raw value in pythonic mode
    """
    if not strict:
        return value

    if isinstance(value, float) and value.is_integer():
        return JoyValue.integer(int(value))
    elif isinstance(value, float):
        return JoyValue.floating(value)
    else:
        return JoyValue.integer(value)


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
        word_name = name or getattr(func, "__name__", "unknown")

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


def python_word(
    name: Optional[str] = None,
    doc: Optional[str] = None,
) -> Callable[[Callable[..., Any]], WordFunc]:
    """
    Decorator for simple auto-pop/push primitives.

    The decorated function receives raw Python values (unwrapped from JoyValue)
    and returns a raw result that is automatically wrapped and pushed.

    Works in both strict and pythonic modes:
    - Strict mode: unwraps JoyValue args, wraps result in JoyValue
    - Pythonic mode: uses raw values throughout

    This is simpler than @joy_word for pure functions that don't need
    direct stack manipulation or ExecutionContext access.

    Args:
        name: Joy word name (defaults to function name)
        doc: Documentation string

    Example:
        @python_word(name="+", doc="N1 N2 -> N3")
        def add(a, b):
            return a + b

        # Usage: 3 4 + -> 7
    """

    def decorator(func: Callable[..., Any]) -> WordFunc:
        word_name = name or getattr(func, "__name__", "unknown")
        sig = inspect.signature(func)
        n_params = len(sig.parameters)

        # Generate specialized wrappers based on param count for performance
        if n_params == 0:

            @wraps(func)
            def wrapper(ctx: ExecutionContext) -> None:
                result = func()
                if result is not None:
                    if ctx.strict:
                        ctx.stack.push_value(python_to_joy(result, strict=True))
                    else:
                        ctx.stack.push(result)

        elif n_params == 1:

            @wraps(func)
            def wrapper(ctx: ExecutionContext) -> None:
                if ctx.stack.depth < 1:
                    raise JoyStackUnderflow(word_name, 1, ctx.stack.depth)
                a = unwrap_value(ctx.stack.pop())
                result = func(a)
                if result is not None:
                    if ctx.strict:
                        ctx.stack.push_value(python_to_joy(result, strict=True))
                    else:
                        ctx.stack.push(result)

        elif n_params == 2:

            @wraps(func)
            def wrapper(ctx: ExecutionContext) -> None:
                if ctx.stack.depth < 2:
                    raise JoyStackUnderflow(word_name, 2, ctx.stack.depth)
                b_raw, a_raw = ctx.stack.pop_n(2)
                a, b = unwrap_value(a_raw), unwrap_value(b_raw)
                result = func(a, b)
                if result is not None:
                    if ctx.strict:
                        ctx.stack.push_value(python_to_joy(result, strict=True))
                    else:
                        ctx.stack.push(result)

        elif n_params == 3:

            @wraps(func)
            def wrapper(ctx: ExecutionContext) -> None:
                if ctx.stack.depth < 3:
                    raise JoyStackUnderflow(word_name, 3, ctx.stack.depth)
                c_raw, b_raw, a_raw = ctx.stack.pop_n(3)
                a, b, c = unwrap_value(a_raw), unwrap_value(b_raw), unwrap_value(c_raw)
                result = func(a, b, c)
                if result is not None:
                    if ctx.strict:
                        ctx.stack.push_value(python_to_joy(result, strict=True))
                    else:
                        ctx.stack.push(result)

        else:
            # Fallback for 4+ params

            @wraps(func)
            def wrapper(ctx: ExecutionContext) -> None:
                if ctx.stack.depth < n_params:
                    raise JoyStackUnderflow(word_name, n_params, ctx.stack.depth)
                raw_args = ctx.stack.pop_n(n_params)
                args = tuple(unwrap_value(arg) for arg in reversed(raw_args))
                result = func(*args)
                if result is not None:
                    if ctx.strict:
                        ctx.stack.push_value(python_to_joy(result, strict=True))
                    else:
                        ctx.stack.push(result)

        # Store metadata
        wrapper.joy_word = word_name  # type: ignore[attr-defined]
        wrapper.joy_params = n_params  # type: ignore[attr-defined]
        wrapper.joy_doc = doc or func.__doc__  # type: ignore[attr-defined]
        wrapper._is_python_word = True  # type: ignore[attr-defined]

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
    - Python namespace (strict=False mode)

    Supports two modes:
    - strict=True (default): Full Joy compliance, values wrapped in JoyValue
    - strict=False: Pythonic mode, any Python object allowed on stack,
                    Python interop syntax enabled (`expr`, $(expr), !stmt)
    """

    def __init__(self, load_stdlib: bool = False, strict: bool = True) -> None:
        self.strict = strict
        self.ctx = ExecutionContext(strict=strict)
        self.ctx.set_evaluator(self)
        self.definitions: Dict[str, JoyQuotation] = {}
        self.undeferror: bool = True  # If True, undefined words raise error
        self.echo_mode: int = 0  # Echo mode for setecho/echo
        self.autoput_mode: int = 1  # Autoput mode for setautoput/autoput (default=1)
        self.joy_argv: list[str] = []  # Joy-specific argv (set when running a file)

        # Python namespace for interop (strict=False mode)
        self._init_python_namespace()

        if load_stdlib:
            self._load_stdlib()

    def _init_python_namespace(self) -> None:
        """Initialize Python namespace for eval/exec in pythonic mode."""
        # Global namespace with useful bindings
        self.python_globals: Dict[str, Any] = {
            "stack": self.ctx.stack,
            "S": self.ctx.stack,
            "ctx": self.ctx,
            "evaluator": self,
            "__builtins__": __builtins__,
        }
        # Local namespace for user-defined variables
        self.python_locals: Dict[str, Any] = {}

        # Pre-import common modules (only in non-strict mode)
        if not self.strict:
            self._python_exec("import math")
            self._python_exec("import json")
            self._python_exec("import os")
            self._python_exec("import re as re_module")

    def _python_exec(self, code: str) -> None:
        """Execute Python statement in the evaluator's namespace."""
        exec(code, self.python_globals, self.python_locals)
        # Merge locals into globals for persistence
        self.python_globals.update(self.python_locals)

    def _python_eval(self, expr: str) -> Any:
        """Evaluate Python expression and return result."""
        return eval(expr, self.python_globals, self.python_locals)

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
        Definitions are processed inline as they're encountered during execution.

        In pythonic mode (strict=False), Python interop syntax is enabled:
        - `expr` or $(expr): Evaluate Python expression, push result
        - !stmt: Execute Python statement (no push)

        Args:
            source: Joy source code string
        """
        # Enable Python interop parsing only in pythonic mode
        parser = Parser(python_interop=not self.strict)
        result = parser.parse_full(source)

        # Execute the program (definitions are inlined and processed as encountered)
        self.execute(result.program)

    def _execute_term(self, term: Any) -> None:
        """
        Execute a single term.

        Args:
            term: Can be JoyValue, JoyQuotation, Definition, PythonExpr,
                  PythonStmt, or string (symbol)
        """
        if isinstance(term, Definition):
            # Register the definition (inline processing)
            self.define(term.name, term.body)

        elif isinstance(term, PythonExpr):
            # Python expression: evaluate and push result
            self._execute_python_expr(term.code)

        elif isinstance(term, PythonStmt):
            # Python statement: execute (no push)
            self._execute_python_stmt(term.code)

        elif isinstance(term, JoyValue):
            # Symbol values should be executed, not pushed
            if term.type == JoyType.SYMBOL:
                self._execute_symbol(term.value)
            else:
                # Other literal values: push to stack
                # In pythonic mode, unwrap the value first
                if self.strict:
                    self.ctx.stack.push_value(term)
                else:
                    self.ctx.stack.push(term.value)

        elif isinstance(term, JoyQuotation):
            # Quotation: wrap and push (don't execute)
            self.ctx.stack.push_value(JoyValue.quotation(term))

        elif isinstance(term, str):
            # Symbol: look up and execute
            self._execute_symbol(term)

        else:
            # Unknown: try to convert and push
            self.ctx.stack.push(term)

    def _execute_python_expr(self, code: str) -> None:
        """
        Execute a Python expression and push the result.

        Args:
            code: Python expression to evaluate

        Raises:
            PythonInteropError: If called in strict mode
        """
        if self.strict:
            raise PythonInteropError(
                "Python interop (`expr` syntax) requires strict=False mode"
            )

        result = self._python_eval(code)
        # Push result to stack (no wrapping in pythonic mode)
        self.ctx.stack.push(result)

    def _execute_python_stmt(self, code: str) -> None:
        """
        Execute a Python statement (no push).

        Args:
            code: Python statement to execute

        Raises:
            PythonInteropError: If called in strict mode
        """
        if self.strict:
            raise PythonInteropError(
                "Python interop (!stmt syntax) requires strict=False mode"
            )

        self._python_exec(code)

    def _execute_symbol(self, name: str) -> None:
        """
        Look up and execute a symbol.

        Args:
            name: Symbol name

        Raises:
            JoyUndefinedWord: If symbol is not defined and undeferror is True
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

        # Undefined word
        if self.undeferror:
            raise JoyUndefinedWord(name)
        # If undeferror is False, push as symbol
        self.ctx.stack.push_value(JoyValue.symbol(name))

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

    def _load_stdlib(self) -> None:
        """Load standard library definitions."""
        import os
        import sys
        from io import StringIO

        stdlib_path = os.path.join(os.path.dirname(__file__), "..", "stdlib")
        # Load inilib first (defines libload, dup2, pop2, etc.), then agglib
        libs = ["inilib.joy", "agglib.joy"]

        # Suppress output during stdlib loading
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            for lib in libs:
                lib_path = os.path.join(stdlib_path, lib)
                if os.path.exists(lib_path):
                    with open(lib_path, "r") as f:
                        source = f.read()
                    parser = Parser()
                    result = parser.parse_full(source)
                    # Execute (definitions are processed inline)
                    self.execute(result.program)
        finally:
            sys.stdout = old_stdout


# Helper function used by many primitives
def expect_quotation(v: JoyValue, op: str) -> JoyQuotation:
    """Extract quotation, raising error if not a quotation or list."""
    if v.type == JoyType.QUOTATION:
        return v.value
    elif v.type == JoyType.LIST:
        # Convert list to quotation for execution
        return JoyQuotation(v.value)
    else:
        raise JoyTypeError(op, "QUOTATION", v.type.name)
