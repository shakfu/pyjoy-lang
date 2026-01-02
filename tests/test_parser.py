"""
Tests for pyjoy.parser module.
"""

import pytest

from pyjoy.errors import JoySetMemberError, JoySyntaxError
from pyjoy.parser import parse
from pyjoy.types import JoyQuotation, JoyType


class TestParser:
    """Tests for the Joy parser."""

    def test_parse_integer(self):
        prog = parse("42")
        assert len(prog.terms) == 1
        assert prog.terms[0].type == JoyType.INTEGER
        assert prog.terms[0].value == 42

    def test_parse_negative_integer(self):
        prog = parse("-17")
        assert prog.terms[0].value == -17

    def test_parse_float(self):
        prog = parse("3.14")
        assert len(prog.terms) == 1
        assert prog.terms[0].type == JoyType.FLOAT
        assert prog.terms[0].value == 3.14

    def test_parse_string(self):
        prog = parse('"hello"')
        assert prog.terms[0].type == JoyType.STRING
        assert prog.terms[0].value == "hello"

    def test_parse_char(self):
        prog = parse("'x'")
        assert prog.terms[0].type == JoyType.CHAR
        assert prog.terms[0].value == "x"

    def test_parse_true(self):
        prog = parse("true")
        assert prog.terms[0].type == JoyType.BOOLEAN
        assert prog.terms[0].value is True

    def test_parse_false(self):
        prog = parse("false")
        assert prog.terms[0].type == JoyType.BOOLEAN
        assert prog.terms[0].value is False

    def test_parse_symbol(self):
        prog = parse("dup")
        assert len(prog.terms) == 1
        assert prog.terms[0] == "dup"  # Symbol is a string

    def test_parse_multiple_terms(self):
        prog = parse("1 2 +")
        assert len(prog.terms) == 3
        assert prog.terms[0].value == 1
        assert prog.terms[1].value == 2
        assert prog.terms[2] == "+"

    def test_parse_quotation(self):
        prog = parse("[1 2]")
        assert len(prog.terms) == 1
        quot = prog.terms[0]
        assert isinstance(quot, JoyQuotation)
        assert len(quot.terms) == 2

    def test_parse_empty_quotation(self):
        prog = parse("[]")
        quot = prog.terms[0]
        assert isinstance(quot, JoyQuotation)
        assert len(quot.terms) == 0

    def test_parse_nested_quotation(self):
        prog = parse("[[1] [2]]")
        outer = prog.terms[0]
        assert isinstance(outer, JoyQuotation)
        assert len(outer.terms) == 2
        assert isinstance(outer.terms[0], JoyQuotation)
        assert isinstance(outer.terms[1], JoyQuotation)

    def test_parse_quotation_with_symbols(self):
        prog = parse("[dup *]")
        quot = prog.terms[0]
        assert quot.terms[0] == "dup"
        assert quot.terms[1] == "*"

    def test_parse_set(self):
        prog = parse("{0 1 2}")
        assert len(prog.terms) == 1
        v = prog.terms[0]
        assert v.type == JoyType.SET
        assert v.value == frozenset({0, 1, 2})

    def test_parse_empty_set(self):
        prog = parse("{}")
        v = prog.terms[0]
        assert v.type == JoyType.SET
        assert v.value == frozenset()

    def test_parse_set_invalid_member(self):
        with pytest.raises(JoySetMemberError):
            parse("{64}")

    def test_parse_set_negative_invalid(self):
        with pytest.raises(JoySetMemberError):
            parse("{-1}")

    def test_unclosed_bracket_raises(self):
        with pytest.raises(JoySyntaxError):
            parse("[1 2")

    def test_unclosed_brace_raises(self):
        with pytest.raises(JoySyntaxError):
            parse("{1 2")

    def test_semicolon_skipped(self):
        prog = parse("1 ; 2")
        assert len(prog.terms) == 2
        assert prog.terms[0].value == 1
        assert prog.terms[1].value == 2

    def test_period_is_print_operator(self):
        prog = parse("1 . 2")
        # "." is the print operator, parsed as a symbol
        assert len(prog.terms) == 3
        assert prog.terms[1] == "."

    def test_complex_expression(self):
        prog = parse("[1 2 3] [dup *] map")
        assert len(prog.terms) == 3

        # First quotation: [1 2 3]
        q1 = prog.terms[0]
        assert isinstance(q1, JoyQuotation)
        assert len(q1.terms) == 3

        # Second quotation: [dup *]
        q2 = prog.terms[1]
        assert isinstance(q2, JoyQuotation)
        assert q2.terms[0] == "dup"

        # Symbol: map
        assert prog.terms[2] == "map"
