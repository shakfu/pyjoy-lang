"""
Tests for pyjoy.scanner module.
"""

from pyjoy.scanner import tokenize


class TestScanner:
    """Tests for the Joy scanner/tokenizer."""

    def test_integer(self):
        tokens = list(tokenize("42"))
        assert len(tokens) == 1
        assert tokens[0].type == "INTEGER"
        assert tokens[0].value == 42

    def test_negative_integer(self):
        tokens = list(tokenize("-17"))
        assert len(tokens) == 1
        assert tokens[0].type == "INTEGER"
        assert tokens[0].value == -17

    def test_float(self):
        tokens = list(tokenize("3.14"))
        assert len(tokens) == 1
        assert tokens[0].type == "FLOAT"
        assert tokens[0].value == 3.14

    def test_float_scientific(self):
        tokens = list(tokenize("1.5e10"))
        assert len(tokens) == 1
        assert tokens[0].type == "FLOAT"
        assert tokens[0].value == 1.5e10

    def test_string(self):
        tokens = list(tokenize('"hello"'))
        assert len(tokens) == 1
        assert tokens[0].type == "STRING"
        assert tokens[0].value == "hello"

    def test_string_with_escapes(self):
        tokens = list(tokenize(r'"hello\nworld"'))
        assert len(tokens) == 1
        assert tokens[0].value == "hello\nworld"

    def test_char(self):
        tokens = list(tokenize("'x'"))
        assert len(tokens) == 1
        assert tokens[0].type == "CHAR"
        assert tokens[0].value == "x"

    def test_char_escape(self):
        tokens = list(tokenize(r"'\n'"))
        assert len(tokens) == 1
        assert tokens[0].value == "\n"

    def test_brackets(self):
        tokens = list(tokenize("[ ]"))
        assert len(tokens) == 2
        assert tokens[0].type == "LBRACKET"
        assert tokens[1].type == "RBRACKET"

    def test_braces(self):
        tokens = list(tokenize("{ }"))
        assert len(tokens) == 2
        assert tokens[0].type == "LBRACE"
        assert tokens[1].type == "RBRACE"

    def test_symbol_identifier(self):
        tokens = list(tokenize("dup"))
        assert len(tokens) == 1
        assert tokens[0].type == "SYMBOL"
        assert tokens[0].value == "dup"

    def test_symbol_with_dash(self):
        tokens = list(tokenize("my-word"))
        assert len(tokens) == 1
        assert tokens[0].type == "SYMBOL"
        assert tokens[0].value == "my-word"

    def test_symbol_operators(self):
        tokens = list(tokenize("+ - * /"))
        assert len(tokens) == 4
        assert all(t.type == "SYMBOL" for t in tokens)
        assert [t.value for t in tokens] == ["+", "-", "*", "/"]

    def test_define(self):
        tokens = list(tokenize("=="))
        assert len(tokens) == 1
        assert tokens[0].type == "DEF_OP"

    def test_semicolon(self):
        tokens = list(tokenize(";"))
        assert len(tokens) == 1
        assert tokens[0].type == "SEMICOLON"

    def test_period(self):
        tokens = list(tokenize("."))
        assert len(tokens) == 1
        assert tokens[0].type == "PERIOD"

    def test_period_not_in_float(self):
        # ".5" should be PERIOD followed by INTEGER
        tokens = list(tokenize(".5"))
        assert tokens[0].type == "PERIOD"

    def test_comment_skipped(self):
        tokens = list(tokenize("1 (* comment *) 2"))
        assert len(tokens) == 2
        assert tokens[0].value == 1
        assert tokens[1].value == 2

    def test_line_comment_skipped(self):
        tokens = list(tokenize("1 # comment\n2"))
        assert len(tokens) == 2
        assert tokens[0].value == 1
        assert tokens[1].value == 2

    def test_whitespace_skipped(self):
        tokens = list(tokenize("  1   2  "))
        assert len(tokens) == 2

    def test_line_tracking(self):
        tokens = list(tokenize("1\n2\n3"))
        assert tokens[0].line == 1
        assert tokens[1].line == 2
        assert tokens[2].line == 3

    def test_column_tracking(self):
        tokens = list(tokenize("abc def"))
        assert tokens[0].column == 0
        assert tokens[1].column == 4

    def test_complex_expression(self):
        source = "[1 2 3] [dup *] map"
        tokens = list(tokenize(source))
        types = [t.type for t in tokens]
        assert types == [
            "LBRACKET",
            "INTEGER",
            "INTEGER",
            "INTEGER",
            "RBRACKET",
            "LBRACKET",
            "SYMBOL",
            "SYMBOL",
            "RBRACKET",
            "SYMBOL",
        ]
