"""
pyjoy.scanner - Lexical analysis for Joy programs.

Tokenizes Joy source code into a stream of tokens.

Supports Python interop syntax (strict=False mode only):
- `expr` : Backtick Python expression (evaluates and pushes result)
- $(expr): Dollar syntax for Python expressions
- !stmt  : Bang statement (executes Python, no push)
"""

from __future__ import annotations

import os
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

    When python_interop=True, also recognizes:
    - PYTHON_EXPR: `expression` (backtick syntax)
    - PYTHON_DOLLAR: $(expression) (dollar syntax)
    - PYTHON_STMT: !statement (bang statement, rest of line)
    """

    # Token patterns in order of precedence
    # Python interop patterns are at the top for priority
    PATTERNS = [
        ("COMMENT", r"\(\*.*?\*\)"),  # (* comment *)
        ("COMMENT2", r"#[^\n]*"),  # # line comment
        # Python interop (must come before other patterns)
        ("PYTHON_EXPR", r"`[^`]*`"),  # `python expression`
        # $(python expression) with nested parens
        ("PYTHON_DOLLAR", r"\$\((?:[^()]*|\([^()]*\))*\)"),
        ("PYTHON_STMT", r"!(?!=)[^\n]*"),  # !stmt (not !=)
        # Special float literals must come before numeric float
        # - for inf/nan: word boundary at end, negative lookahead for ==
        # - for -inf: preceded by non-word char or start, word boundary at end
        ("FLOAT_SPECIAL", r"(?:(?<![a-zA-Z0-9_])-inf|(?<![a-zA-Z0-9_])inf|(?<![a-zA-Z0-9_])nan)(?![a-zA-Z0-9_])(?!\s*==)"),  # inf, -inf, nan
        ("FLOAT", r"-?\d+\.\d+(?:[eE][+-]?\d+)?"),  # 3.14, -2.5e10
        ("INTEGER", r"-?\d+"),  # 42, -17
        ("STRING", r'"(?:[^"\\]|\\.)*"'),  # "hello"
        # Character literal: 'x' or 'x (Joy-style) with escape sequences
        # including octal \nnn
        (
            "CHAR",
            r"'(?:[^'\\]|\\[0-7]{1,3}|\\.)(?:'|(?=\s|$))|'(?:[^'\s\\]|\\[0-7]{1,3}|\\.)",
        ),
        ("LBRACKET", r"\["),  # [
        ("RBRACKET", r"\]"),  # ]
        ("LBRACE", r"\{"),  # {
        ("RBRACE", r"\}"),  # }
        ("SEMICOLON", r";"),  # ;
        ("PERIOD", r"\."),  # .
        ("DEF_OP", r"=="),  # == (definition operator)
        # Keywords must come before SYMBOL to match first
        ("DEFINE_KW", r"\b(?:DEFINE|LIBRA|CONST)\b"),  # DEFINE, LIBRA, or CONST keyword
        ("HIDE_KW", r"\bHIDE\b"),  # HIDE keyword
        ("IN_KW", r"\bIN\b"),  # IN keyword
        ("PUBLIC_KW", r"\bPUBLIC\b"),  # PUBLIC keyword
        ("PRIVATE_KW", r"\bPRIVATE\b"),  # PRIVATE keyword
        ("END_KW", r"\bEND\b"),  # END keyword
        ("MODULE_KW", r"\bMODULE\b"),  # MODULE keyword
        # Word: identifier or operator symbols
        # Also allow -name pattern for symbols like -inf
        (
            "SYMBOL",
            r"[a-zA-Z_][a-zA-Z0-9_\-]*|-[a-zA-Z_][a-zA-Z0-9_\-]*|[+\-*/<=>&|?@#%^~:!]+",
        ),  # noqa: E501
        ("WHITESPACE", r"\s+"),  # whitespace
    ]

    def __init__(self, python_interop: bool = False) -> None:
        """
        Initialize the scanner.

        Args:
            python_interop: If True, recognize Python interop tokens.
                           If False (default), treat them as regular symbols/errors.
        """
        self.python_interop = python_interop
        # Compile the combined regex pattern
        pattern = "|".join(f"(?P<{name}>{pat})" for name, pat in self.PATTERNS)
        self._regex = re.compile(pattern, re.DOTALL)

    def tokenize(
        self, source: str, execute_shell: bool = True
    ) -> Iterator[Token]:
        """
        Generate tokens from source code.

        Args:
            source: Joy source code
            execute_shell: If True, execute shell escape lines ($ at line start)

        Yields:
            Token objects

        Skips whitespace and comments.
        Shell escape lines (starting with $) are executed and removed.

        Python interop tokens (backticks, $(), !) are only yielded when
        python_interop=True was set in __init__.
        """
        # Pre-process shell escape lines
        source = self._process_shell_escapes(source, execute_shell)

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

            # Handle Python interop tokens
            if kind == "PYTHON_EXPR":
                if not self.python_interop:
                    # Skip in strict mode - this will cause a parse error
                    # which is the desired behavior
                    continue
                # Extract expression from backticks: `expr` -> expr
                value = value[1:-1]
            elif kind == "PYTHON_DOLLAR":
                if not self.python_interop:
                    continue
                # Extract expression from $(expr) -> expr
                value = value[2:-1]
            elif kind == "PYTHON_STMT":
                if not self.python_interop:
                    continue
                # Extract statement from !stmt -> stmt (strip leading !)
                value = value[1:].strip()

            # Convert token values
            elif kind == "INTEGER":
                value = int(value)
            elif kind == "FLOAT_SPECIAL":
                # Convert inf, -inf, nan to float values
                kind = "FLOAT"  # Normalize to FLOAT token type
                value = float(value)
            elif kind == "FLOAT":
                value = float(value)
            elif kind == "STRING":
                value = self._unescape_string(value[1:-1])
            elif kind == "CHAR":
                # Handle both 'x' and 'x (Joy-style without closing quote)
                if value.endswith("'") and len(value) > 2:
                    value = self._unescape_char(value[1:-1])
                else:
                    value = self._unescape_char(value[1:])

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

    def _process_shell_escapes(self, source: str, execute: bool) -> str:
        """
        Process shell escape lines (lines starting with $).

        In Joy, a line starting with $ at column 0 executes the rest
        of the line as a shell command and is not part of the program.

        Exception: $(expr) is Python interop syntax, not shell escape.

        Args:
            source: Joy source code
            execute: If True, actually execute shell commands

        Returns:
            Source with shell escape lines removed
        """
        lines = source.split("\n")
        result_lines = []

        for line in lines:
            # Shell escape: $ at start of line, but NOT $( which is Python interop
            if line.startswith("$") and not line.startswith("$("):
                # Shell escape: execute the command (everything after $)
                if execute:
                    cmd = line[1:].strip()
                    if cmd:
                        os.system(cmd)
                # Don't include this line in the output
                result_lines.append("")  # Keep line count consistent
            else:
                result_lines.append(line)

        return "\n".join(result_lines)


# Convenience function for one-shot tokenization
def tokenize(source: str, python_interop: bool = False) -> Iterator[Token]:
    """
    Tokenize Joy source code.

    Args:
        source: Joy source code
        python_interop: If True, recognize Python interop tokens

    Yields:
        Token objects
    """
    scanner = Scanner(python_interop=python_interop)
    return scanner.tokenize(source)
