"""
pyjoy.evaluator.core - Core evaluator infrastructure.

Contains:
- joy_word decorator for defining primitives
- Evaluator class for executing Joy programs
- Primitive registry functions
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, Optional

from pyjoy.errors import JoyStackUnderflow, JoyTypeError, JoyUndefinedWord
from pyjoy.parser import Definition, Parser
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

    def __init__(self, load_stdlib: bool = False) -> None:
        self.ctx = ExecutionContext()
        self.ctx.set_evaluator(self)
        self.definitions: Dict[str, JoyQuotation] = {}
        self.undeferror: bool = True  # If True, undefined words raise error
        self.echo_mode: int = 0  # Echo mode for setecho/echo
        self.autoput_mode: int = 0  # Autoput mode for setautoput/autoput
        if load_stdlib:
            self._load_stdlib()

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

        Args:
            source: Joy source code string
        """
        parser = Parser()
        result = parser.parse_full(source)

        # Execute the program (definitions are inlined and processed as encountered)
        self.execute(result.program)

    def _execute_term(self, term: Any) -> None:
        """
        Execute a single term.

        Args:
            term: Can be JoyValue, JoyQuotation, Definition, or string (symbol)
        """
        if isinstance(term, Definition):
            # Register the definition (inline processing)
            self.define(term.name, term.body)

        elif isinstance(term, JoyValue):
            # Symbol values should be executed, not pushed
            if term.type == JoyType.SYMBOL:
                self._execute_symbol(term.value)
            else:
                # Other literal values: push to stack
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
