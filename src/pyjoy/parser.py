"""
pyjoy.parser - Parser for Joy programs.

Converts a token stream into an AST (nested structure of terms).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Set

from pyjoy.errors import JoySetMemberError, JoySyntaxError
from pyjoy.scanner import Scanner, Token
from pyjoy.types import JoyQuotation, JoyValue

# Sentinel for terms to skip
_SKIP = object()


@dataclass
class Definition:
    """A user-defined word: name == body."""

    name: str
    body: JoyQuotation


@dataclass
class ParseResult:
    """Result of parsing Joy source code."""

    definitions: List[Definition]
    program: JoyQuotation


class Parser:
    """
    Joy parser: converts token stream to AST.

    AST is a JoyQuotation containing:
    - JoyValue literals (integers, floats, strings, etc.)
    - JoyQuotation for [...] blocks
    - Strings for symbols (resolved at runtime)
    """

    def __init__(self) -> None:
        self._tokens: List[Token] = []
        self._pos: int = 0

    def parse(self, source: str) -> JoyQuotation:
        """
        Parse source code into a program (backward compatible).

        Args:
            source: Joy source code

        Returns:
            JoyQuotation representing the program
        """
        result = self.parse_full(source)
        return result.program

    def parse_full(self, source: str) -> ParseResult:
        """
        Parse source code into definitions and program.

        Definitions are inlined into the program at their original positions.
        This ensures code executed before a definition uses the prior definition,
        not the later one.

        Args:
            source: Joy source code

        Returns:
            ParseResult with definitions inlined in program
        """
        scanner = Scanner()
        self._tokens = list(scanner.tokenize(source))
        self._pos = 0

        terms: List[Any] = []

        while self._current() is not None:
            token = self._current()

            # Check for DEFINE/LIBRA block - inline definitions into program
            if token and token.type == "DEFINE_KW":
                defs = self._parse_definition_block()
                terms.extend(defs)  # Inline Definition objects
            # Check for HIDE block
            elif token and token.type == "HIDE_KW":
                defs = self._parse_hide_block()
                terms.extend(defs)  # Inline Definition objects
            else:
                # Parse regular terms
                term = self._parse_term()
                if term is not _SKIP:
                    terms.append(term)

        # definitions field kept empty for backwards compat - all defs are in program
        return ParseResult([], JoyQuotation(tuple(terms)))

    def _current(self) -> Optional[Token]:
        """Get current token or None if at end."""
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self) -> Optional[Token]:
        """Consume and return current token."""
        token = self._current()
        self._pos += 1
        return token

    def _parse_terms(self, terminators: Set[str]) -> List[Any]:
        """
        Parse sequence of terms until a terminator token.

        Args:
            terminators: Set of token types that end the sequence

        Returns:
            List of terms
        """
        terms: List[Any] = []

        while True:
            token = self._current()
            if token is None or token.type in terminators:
                break

            term = self._parse_term()
            if term is not _SKIP:
                terms.append(term)

        return terms

    def _parse_definition_block(self) -> List[Definition]:
        """
        Parse a DEFINE/LIBRA block.

        Syntax:
            DEFINE name1 == body1; name2 == body2 .
            DEFINE name == body .

        Also handles PUBLIC and PRIVATE modifiers.

        Returns:
            List of Definition objects
        """
        start_token = self._advance()  # Consume DEFINE/LIBRA
        assert start_token is not None

        definitions: List[Definition] = []
        _is_public = True  # Default visibility (not yet implemented)

        while True:
            token = self._current()
            if token is None:
                break

            # Handle visibility modifiers (parsed but not yet implemented)
            if token.type == "PUBLIC_KW":
                self._advance()
                _is_public = True
                continue
            elif token.type == "PRIVATE_KW":
                self._advance()
                _is_public = False
                continue
            elif token.type == "END_KW":
                self._advance()
                break

            # End of definition block
            if token.type == "PERIOD":
                self._advance()
                break

            # Expect a symbol (name)
            if token.type != "SYMBOL":
                raise JoySyntaxError(
                    f"Expected name in definition, got {token.type}",
                    token.line,
                    token.column,
                )

            name = token.value
            self._advance()

            # Expect ==
            token = self._current()
            if token is None or token.type != "DEF_OP":
                raise JoySyntaxError(
                    "Expected '==' after name in definition",
                    start_token.line,
                    start_token.column,
                )
            self._advance()

            # Parse body until ; or .
            body_terms = self._parse_terms({"SEMICOLON", "PERIOD", "DEFINE_KW"})
            body = JoyQuotation(tuple(body_terms))

            definitions.append(Definition(name, body))

            # Check for separator
            token = self._current()
            if token is None:
                break
            if token.type == "SEMICOLON":
                self._advance()
                continue
            elif token.type == "PERIOD":
                self._advance()
                break
            elif token.type == "DEFINE_KW":
                # Another DEFINE block starts - don't consume it
                break
            else:
                # Continue parsing more definitions or body terms
                continue

        return definitions

    def _parse_hide_block(self) -> List[Definition]:
        """
        Parse a HIDE/IN/END block.

        Syntax:
            HIDE
                hidden_name == hidden_body;
                ...
            IN
                public_name == public_body;
                ...
            END.

        Hidden definitions are included but could be filtered later.
        For now, we include all definitions (both hidden and public).

        Returns:
            List of Definition objects (both hidden and public)
        """
        self._advance()  # Consume HIDE

        definitions: List[Definition] = []

        # Parse hidden definitions until IN
        while True:
            token = self._current()
            if token is None:
                break

            if token.type == "IN_KW":
                self._advance()
                break

            if token.type == "END_KW":
                self._advance()
                # Check for trailing period
                token = self._current()
                if token and token.type == "PERIOD":
                    self._advance()
                return definitions

            if token.type == "SYMBOL":
                # Parse a definition
                name = token.value
                self._advance()

                token = self._current()
                if token is None or token.type != "DEF_OP":
                    continue
                self._advance()

                body_terms = self._parse_terms(
                    {"SEMICOLON", "IN_KW", "END_KW", "PERIOD"}
                )
                body = JoyQuotation(tuple(body_terms))
                definitions.append(Definition(name, body))

                token = self._current()
                if token and token.type == "SEMICOLON":
                    self._advance()
            else:
                # Skip other tokens in HIDE section
                self._advance()

        # Parse public definitions until END
        while True:
            token = self._current()
            if token is None:
                break

            if token.type == "END_KW":
                self._advance()
                # Check for trailing period
                token = self._current()
                if token and token.type == "PERIOD":
                    self._advance()
                break

            if token.type == "SYMBOL":
                # Parse a definition
                name = token.value
                self._advance()

                token = self._current()
                if token is None or token.type != "DEF_OP":
                    continue
                self._advance()

                body_terms = self._parse_terms({"SEMICOLON", "END_KW", "PERIOD"})
                body = JoyQuotation(tuple(body_terms))
                definitions.append(Definition(name, body))

                token = self._current()
                if token and token.type == "SEMICOLON":
                    self._advance()
            else:
                # Skip other tokens
                self._advance()

        return definitions

    def _parse_term(self) -> Any:
        """
        Parse a single term.

        Returns:
            JoyValue, JoyQuotation, string (symbol), or _SKIP
        """
        token = self._current()
        if token is None:
            return _SKIP

        if token.type == "INTEGER":
            self._advance()
            return JoyValue.integer(token.value)

        elif token.type == "FLOAT":
            self._advance()
            return JoyValue.floating(token.value)

        elif token.type == "STRING":
            self._advance()
            return JoyValue.string(token.value)

        elif token.type == "CHAR":
            self._advance()
            return JoyValue.char(token.value)

        elif token.type == "LBRACKET":
            return self._parse_quotation()

        elif token.type == "LBRACE":
            return self._parse_set()

        elif token.type == "SYMBOL":
            self._advance()
            name = token.value

            # Handle boolean literals
            if name == "true":
                return JoyValue.boolean(True)
            elif name == "false":
                return JoyValue.boolean(False)

            # Return as symbol string (late binding - resolved at runtime)
            return name

        elif token.type == "SEMICOLON":
            # Statement separator - skip
            self._advance()
            return _SKIP

        elif token.type == "PERIOD":
            # Period is the print operator (.) in executable code
            self._advance()
            return "."

        elif token.type == "DEF_OP":
            # == should only appear in definition context, skip if stray
            self._advance()
            return _SKIP

        elif token.type in (
            "DEFINE_KW",
            "PUBLIC_KW",
            "PRIVATE_KW",
            "END_KW",
            "HIDE_KW",
            "IN_KW",
            "MODULE_KW",
        ):
            # Keywords - skip when encountered outside definition context
            self._advance()
            return _SKIP

        else:
            raise JoySyntaxError(
                f"Unexpected token: {token.type}",
                token.line,
                token.column,
            )

    def _parse_quotation(self) -> JoyQuotation:
        """
        Parse a quotation [...].

        Returns:
            JoyQuotation containing the parsed terms
        """
        start_token = self._advance()  # Consume '['
        assert start_token is not None

        terms = self._parse_terms({"RBRACKET"})

        end_token = self._current()
        if end_token is None or end_token.type != "RBRACKET":
            raise JoySyntaxError(
                "Expected ']'",
                start_token.line,
                start_token.column,
            )
        self._advance()  # Consume ']'

        return JoyQuotation(tuple(terms))

    def _parse_set(self) -> JoyValue:
        """
        Parse a set literal {...}.

        Set members must be integers in the range [0, 63].

        Returns:
            JoyValue of type SET
        """
        start_token = self._advance()  # Consume '{'
        assert start_token is not None

        terms = self._parse_terms({"RBRACE"})

        end_token = self._current()
        if end_token is None or end_token.type != "RBRACE":
            raise JoySyntaxError(
                "Expected '}'",
                start_token.line,
                start_token.column,
            )
        self._advance()  # Consume '}'

        # Convert to set of integers
        members: Set[int] = set()
        for term in terms:
            if isinstance(term, JoyValue) and term.type.name == "INTEGER":
                member = term.value
                if not (0 <= member <= 63):
                    raise JoySetMemberError(member)
                members.add(member)
            else:
                raise JoySyntaxError(
                    "Set members must be integers in range [0, 63]",
                    start_token.line,
                    start_token.column,
                )

        return JoyValue.joy_set(frozenset(members))


def parse(source: str) -> JoyQuotation:
    """
    Parse Joy source code into a program.

    Args:
        source: Joy source code

    Returns:
        JoyQuotation representing the program
    """
    parser = Parser()
    return parser.parse(source)
