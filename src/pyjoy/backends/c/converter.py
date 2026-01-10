"""
pyjoy.backends.c.converter - Converts Joy AST to C code representation.

This module transforms parsed Joy programs into a representation that can
be emitted as C code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...parser import Definition
from ...types import JoyQuotation, JoyType, JoyValue


@dataclass
class CValue:
    """Represents a Joy value in C code."""

    # "integer", "float", "boolean", "char", "string", "list", "set",
    # "quotation", "symbol"
    type: str
    value: Any

    def to_c_init(self) -> str:
        """Generate C initializer for this value."""
        if self.type == "integer":
            return f"joy_integer({self.value})"
        elif self.type == "float":
            import math
            if math.isinf(self.value):
                if self.value > 0:
                    return "joy_float(INFINITY)"
                else:
                    return "joy_float(-INFINITY)"
            elif math.isnan(self.value):
                return "joy_float(NAN)"
            else:
                return f"joy_float({self.value})"
        elif self.type == "boolean":
            return f"joy_boolean({'true' if self.value else 'false'})"
        elif self.type == "char":
            c = self.value
            if c == "\n":
                return "joy_char('\\n')"
            elif c == "\t":
                return "joy_char('\\t')"
            elif c == "\r":
                return "joy_char('\\r')"
            elif c == "\\":
                return "joy_char('\\\\')"
            elif c == "'":
                return "joy_char('\\'')"
            else:
                return f"joy_char('{c}')"
        elif self.type == "string":
            escaped = (
                self.value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\t", "\\t")
            )
            return f'joy_string("{escaped}")'
        elif self.type == "set":
            members = ", ".join(str(m) for m in sorted(self.value))
            return f"joy_set_from((int[]){{{members}}}, {len(self.value)})"
        elif self.type == "symbol":
            return f'joy_symbol("{self.value}")'
        elif self.type == "quotation":
            # Quotation values are handled specially by the emitter
            return f"/* quotation with {len(self.value)} terms */"
        elif self.type == "list":
            return f"/* list with {len(self.value)} items */"
        else:
            return f"/* unknown type: {self.type} */"


@dataclass
class CQuotation:
    """Represents a Joy quotation compiled to C."""

    name: str  # C variable name for this quotation
    terms: list[CValue] = field(default_factory=list)

    def add_term(self, term: CValue) -> None:
        """Add a term to the quotation."""
        self.terms.append(term)


@dataclass
class CDefinition:
    """Represents a user-defined Joy word compiled to C."""

    name: str  # Joy word name
    c_name: str  # C function name
    body: CQuotation  # Body as quotation


@dataclass
class CProgram:
    """Complete C program representation."""

    quotations: list[CQuotation] = field(default_factory=list)
    definitions: list[CDefinition] = field(default_factory=list)
    main_body: CQuotation | None = None

    def add_quotation(self, quotation: CQuotation) -> None:
        """Add a quotation to the program."""
        self.quotations.append(quotation)

    def add_definition(self, definition: CDefinition) -> None:
        """Add a definition to the program."""
        self.definitions.append(definition)


class JoyToCConverter:
    """
    Converts Joy AST to C representation.

    This converter transforms parsed Joy programs into CProgram objects
    that can be emitted as C code by the CEmitter.
    """

    def __init__(self) -> None:
        self._quotation_counter = 0
        self._program: CProgram | None = None

    def _next_quotation_name(self) -> str:
        """Generate a unique name for a quotation."""
        name = f"_quot_{self._quotation_counter}"
        self._quotation_counter += 1
        return name

    def _sanitize_name(self, name: str) -> str:
        """Convert Joy word name to valid C identifier."""
        # Replace non-alphanumeric characters
        result = []
        for c in name:
            if c.isalnum():
                result.append(c)
            elif c == "-":
                result.append("_")
            elif c == "+":
                result.append("_plus")
            elif c == "*":
                result.append("_star")
            elif c == "/":
                result.append("_slash")
            elif c == "=":
                result.append("_eq")
            elif c == "<":
                result.append("_lt")
            elif c == ">":
                result.append("_gt")
            elif c == "!":
                result.append("_bang")
            elif c == "?":
                result.append("_quest")
            elif c == "@":
                result.append("_at")
            elif c == "#":
                result.append("_hash")
            elif c == "$":
                result.append("_dollar")
            elif c == "%":
                result.append("_percent")
            elif c == "^":
                result.append("_caret")
            elif c == "&":
                result.append("_amp")
            elif c == "|":
                result.append("_pipe")
            elif c == "~":
                result.append("_tilde")
            elif c == ":":
                result.append("_colon")
            else:
                result.append("_")

        name = "".join(result)

        # Ensure it doesn't start with a digit
        if name and name[0].isdigit():
            name = "_" + name

        return name or "_unnamed"

    def convert(
        self, program: JoyQuotation, definitions: dict[str, JoyQuotation] | None = None
    ) -> CProgram:
        """
        Convert a Joy program to C representation.

        Args:
            program: The main program as a quotation
            definitions: User-defined words (name -> body)

        Returns:
            CProgram ready for C emission
        """
        self._quotation_counter = 0
        self._program = CProgram()

        # Convert user definitions
        if definitions:
            for name, body in definitions.items():
                c_def = self._convert_definition(name, body)
                self._program.add_definition(c_def)

        # Convert main program
        self._program.main_body = self._convert_quotation(program, "_main_program")

        return self._program

    def _convert_definition(self, name: str, body: JoyQuotation) -> CDefinition:
        """Convert a Joy definition to C."""
        c_name = f"joy_word_{self._sanitize_name(name)}"
        c_body = self._convert_quotation(body, c_name + "_body")
        return CDefinition(name=name, c_name=c_name, body=c_body)

    def _convert_quotation(
        self, quotation: JoyQuotation, name: str | None = None
    ) -> CQuotation:
        """Convert a Joy quotation to C."""
        if name is None:
            name = self._next_quotation_name()

        c_quot = CQuotation(name=name)

        for term in quotation.terms:
            # Skip Definition objects - they're handled separately
            if isinstance(term, Definition):
                continue
            c_value = self._convert_value(term)
            c_quot.add_term(c_value)

        # Note: Nested quotations are added to program's quotation list
        # in _convert_value when they are encountered
        return c_quot

    def _convert_value(self, value: JoyValue | str | JoyQuotation) -> CValue:
        """Convert a Joy value to C representation."""
        # Handle string symbols (late-bound symbols from parser)
        if isinstance(value, str):
            return CValue(type="symbol", value=value)

        # Handle raw JoyQuotation (nested quotation from parser)
        if isinstance(value, JoyQuotation):
            nested = self._convert_quotation(value)
            if self._program:
                self._program.add_quotation(nested)
            return CValue(type="quotation", value=nested)

        if value.type == JoyType.INTEGER:
            return CValue(type="integer", value=value.value)

        elif value.type == JoyType.FLOAT:
            return CValue(type="float", value=value.value)

        elif value.type == JoyType.BOOLEAN:
            return CValue(type="boolean", value=value.value)

        elif value.type == JoyType.CHAR:
            return CValue(type="char", value=value.value)

        elif value.type == JoyType.STRING:
            return CValue(type="string", value=value.value)

        elif value.type == JoyType.SYMBOL:
            return CValue(type="symbol", value=value.value)

        elif value.type == JoyType.SET:
            # Set is a frozenset of integers
            members = list(value.value) if value.value else []
            return CValue(type="set", value=members)

        elif value.type == JoyType.QUOTATION:
            # Recursively convert nested quotation
            nested = self._convert_quotation(value.value)
            if self._program:
                self._program.add_quotation(nested)
            return CValue(type="quotation", value=nested)

        elif value.type == JoyType.LIST:
            # Convert list items
            items = [self._convert_value(item) for item in value.value]
            return CValue(type="list", value=items)

        else:
            raise ValueError(f"Unknown Joy type: {value.type}")

    def convert_source(self, source: str) -> CProgram:
        """
        Convert Joy source code to C representation.

        This is a convenience method that parses and converts in one step.

        Args:
            source: Joy source code

        Returns:
            CProgram ready for C emission
        """
        from ...parser import Definition, Parser

        parser = Parser()
        result = parser.parse_full(source)

        # Extract definitions from program terms (they're now inlined)
        definitions = {
            t.name: t.body for t in result.program.terms if isinstance(t, Definition)
        }

        return self.convert(result.program, definitions)
