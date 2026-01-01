"""
pyjoy.scanner - Lexical analysis for Joy programs.

Tokenizes Joy source code into a stream of tokens.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterator


@dataclass(slots=True)
class Token:
    """A lexical token from Joy source code."""

    type: str
    value: Any
    line: int
    column: int


class Scanner:
    """
    Joy lexical analyzer.

    Converts source code into a stream of tokens.
    """

    # Token patterns in order of precedence
    PATTERNS = [
        ("COMMENT", r"\(\*.*?\*\)"),  # (* comment *)
        ("COMMENT2", r"#[^\n]*"),  # # line comment
        ("FLOAT", r"-?\d+\.\d+(?:[eE][+-]?\d+)?"),  # 3.14, -2.5e10
        ("INTEGER", r"-?\d+"),  # 42, -17
        ("STRING", r'"(?:[^"\\]|\\.)*"'),  # "hello"
        ("CHAR", r"'(?:[^'\\]|\\.)'"),  # 'x', '\n'
        ("LBRACKET", r"\["),  # [
        ("RBRACKET", r"\]"),  # ]
        ("LBRACE", r"\{"),  # {
        ("RBRACE", r"\}"),  # }
        ("SEMICOLON", r";"),  # ;
        ("PERIOD", r"\."),  # .
        ("DEF_OP", r"=="),  # == (definition operator)
        # Keywords must come before SYMBOL to match first
        ("DEFINE_KW", r"\b(?:DEFINE|LIBRA)\b"),  # DEFINE or LIBRA keyword
        ("PUBLIC_KW", r"\bPUBLIC\b"),  # PUBLIC keyword
        ("PRIVATE_KW", r"\bPRIVATE\b"),  # PRIVATE keyword
        ("END_KW", r"\bEND\b"),  # END keyword
        # Word: identifier or operator symbols
        ("SYMBOL", r"[a-zA-Z_][a-zA-Z0-9_\-]*|[+\-*/<=>&|!?@#$%^~:]+"),
        ("WHITESPACE", r"\s+"),  # whitespace
    ]

    def __init__(self) -> None:
        # Compile the combined regex pattern
        pattern = "|".join(f"(?P<{name}>{pat})" for name, pat in self.PATTERNS)
        self._regex = re.compile(pattern, re.DOTALL)

    def tokenize(self, source: str) -> Iterator[Token]:
        """
        Generate tokens from source code.

        Args:
            source: Joy source code

        Yields:
            Token objects

        Skips whitespace and comments.
        """
        line = 1
        line_start = 0

        for match in self._regex.finditer(source):
            kind = match.lastgroup
            value: Any = match.group()
            column = match.start() - line_start

            # Track line numbers for newlines in the match
            newlines = value.count("\n")
            if newlines:
                line += newlines
                # Find the position after the last newline
                last_newline = value.rfind("\n")
                line_start = match.start() + last_newline + 1

            # Skip whitespace and comments
            if kind in ("WHITESPACE", "COMMENT", "COMMENT2"):
                continue

            assert kind is not None

            # Convert token values
            if kind == "INTEGER":
                value = int(value)
            elif kind == "FLOAT":
                value = float(value)
            elif kind == "STRING":
                value = self._unescape_string(value[1:-1])
            elif kind == "CHAR":
                value = self._unescape_char(value[1:-1])

            yield Token(kind, value, line, column)

    def _unescape_string(self, s: str) -> str:
        """
        Process escape sequences in a string literal.

        Handles: \\n, \\t, \\r, \\\\, \\", etc.
        """
        # Use Python's unicode_escape codec for standard escapes
        try:
            return s.encode("utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            # If that fails, return as-is
            return s

    def _unescape_char(self, c: str) -> str:
        """
        Process escape sequences in a character literal.

        Handles: \\n, \\t, \\r, \\\\, \\', etc.
        """
        if c.startswith("\\"):
            return self._unescape_string(c)
        return c


# Convenience function for one-shot tokenization
def tokenize(source: str) -> Iterator[Token]:
    """
    Tokenize Joy source code.

    Args:
        source: Joy source code

    Yields:
        Token objects
    """
    scanner = Scanner()
    return scanner.tokenize(source)
