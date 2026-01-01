"""
Tests for Phase 6 definitions and module system.
"""

from pyjoy.parser import Parser
from pyjoy.types import JoyType


class TestDefinitionParsing:
    """Tests for parsing definitions."""

    def test_parse_simple_definition(self):
        """DEFINE name == body . parses correctly."""
        parser = Parser()
        result = parser.parse_full("DEFINE square == dup * .")
        assert len(result.definitions) == 1
        assert result.definitions[0].name == "square"
        assert len(result.definitions[0].body.terms) == 2

    def test_parse_multiple_definitions(self):
        """DEFINE name1 == body1; name2 == body2 . parses correctly."""
        parser = Parser()
        result = parser.parse_full("DEFINE square == dup *; cube == dup dup * * .")
        assert len(result.definitions) == 2
        assert result.definitions[0].name == "square"
        assert result.definitions[1].name == "cube"

    def test_parse_libra_keyword(self):
        """LIBRA is an alias for DEFINE."""
        parser = Parser()
        result = parser.parse_full("LIBRA double == 2 * .")
        assert len(result.definitions) == 1
        assert result.definitions[0].name == "double"

    def test_parse_definitions_with_program(self):
        """Definitions and program code both parse."""
        parser = Parser()
        result = parser.parse_full("DEFINE square == dup * . 5 square")
        assert len(result.definitions) == 1
        assert len(result.program.terms) == 2

    def test_parse_empty_body(self):
        """Definition with empty body is valid."""
        parser = Parser()
        result = parser.parse_full("DEFINE nop == .")
        assert len(result.definitions) == 1
        assert result.definitions[0].name == "nop"
        assert len(result.definitions[0].body.terms) == 0

    def test_parse_definition_with_quotation(self):
        """Definition containing quotation parses correctly."""
        parser = Parser()
        result = parser.parse_full("DEFINE square-list == [dup *] map .")
        assert len(result.definitions) == 1
        # Body should have 2 terms: quotation and 'map'
        assert len(result.definitions[0].body.terms) == 2


class TestDefinitionExecution:
    """Tests for executing definitions."""

    def test_simple_definition(self, evaluator):
        """Simple definition works."""
        evaluator.run("DEFINE square == dup * . 5 square")
        assert evaluator.stack.peek().value == 25

    def test_multiple_definitions(self, evaluator):
        """Multiple definitions in one block work."""
        evaluator.run("DEFINE square == dup *; cube == dup dup * * . 3 cube")
        assert evaluator.stack.peek().value == 27

    def test_nested_definitions(self, evaluator):
        """Definitions can use other definitions."""
        evaluator.run("DEFINE square == dup *; quad == square square . 2 quad")
        assert evaluator.stack.peek().value == 16

    def test_definition_with_stack_ops(self, evaluator):
        """Definition using stack operations."""
        evaluator.run("DEFINE rot3 == rolldown . 1 2 3 rot3")
        # Stack was [1 2 3] (3 is TOS)
        # rolldown: [X Y Z] -> [Y Z X], so [1 2 3] -> [2 3 1]
        result = [evaluator.stack.pop().value for _ in range(3)]
        # Popping from TOS: 1, 3, 2
        assert result == [1, 3, 2]

    def test_definition_with_conditionals(self, evaluator):
        """Definition using conditionals."""
        evaluator.run("DEFINE abs == dup 0 < [0 swap -] [] ifte . -5 abs")
        assert evaluator.stack.peek().value == 5

    def test_recursive_definition(self, evaluator):
        """Definition can be recursive."""
        evaluator.run("""
            DEFINE factorial == [0 =] [pop 1] [dup 1 - factorial *] ifte .
            5 factorial
        """)
        assert evaluator.stack.peek().value == 120

    def test_libra_execution(self, evaluator):
        """LIBRA works as alias for DEFINE."""
        evaluator.run("LIBRA double == 2 * . 7 double")
        assert evaluator.stack.peek().value == 14

    def test_definition_empty_body(self, evaluator):
        """Definition with empty body does nothing."""
        evaluator.run("DEFINE nop == . 42 nop")
        assert evaluator.stack.peek().value == 42

    def test_multiple_define_blocks(self, evaluator):
        """Multiple DEFINE blocks work."""
        evaluator.run("""
            DEFINE square == dup * .
            DEFINE cube == dup dup * * .
            3 square cube
        """)
        # 3 square = 9, 9 cube = 729
        assert evaluator.stack.peek().value == 729


class TestDefinitionEdgeCases:
    """Edge cases for definitions."""

    def test_redefine_word(self, evaluator):
        """Redefining a word uses the new definition."""
        evaluator.run("DEFINE foo == 1 . DEFINE foo == 2 . foo")
        assert evaluator.stack.peek().value == 2

    def test_definition_without_period(self, evaluator):
        """Definition without period should still parse (EOF terminates)."""
        parser = Parser()
        result = parser.parse_full("DEFINE foo == 42")
        assert len(result.definitions) == 1
        assert result.definitions[0].name == "foo"

    def test_definition_with_literals(self, evaluator):
        """Definition can contain various literals."""
        evaluator.run('DEFINE constants == 42 3.14 "hello" . constants')
        evaluator.stack.pop()  # "hello"
        evaluator.stack.pop()  # 3.14
        assert evaluator.stack.pop().value == 42

    def test_definition_with_set(self, evaluator):
        """Definition can contain sets."""
        evaluator.run("DEFINE my-set == {1 2 3} . my-set")
        result = evaluator.stack.peek()
        assert result.type == JoyType.SET
        assert 1 in result.value and 2 in result.value and 3 in result.value

    def test_definition_shadowing_primitive(self, evaluator):
        """Definition can shadow a primitive (primitives take precedence)."""
        # Actually, in our implementation primitives are checked first
        # So this test verifies that behavior
        evaluator.run("DEFINE dup == 999 . 5 dup")
        # dup primitive should still work
        assert evaluator.stack.pop().value == 5
        assert evaluator.stack.pop().value == 5


class TestDefinitionSyntax:
    """Tests for various definition syntax forms."""

    def test_semicolon_separator(self, evaluator):
        """Semicolon separates multiple definitions."""
        evaluator.run("DEFINE a == 1; b == 2; c == 3 . a b c")
        assert evaluator.stack.pop().value == 3
        assert evaluator.stack.pop().value == 2
        assert evaluator.stack.pop().value == 1

    def test_complex_body(self, evaluator):
        """Complex body with multiple operations."""
        evaluator.run("""
            DEFINE fib ==
                [2 <]
                []
                [dup 1 - fib swap 2 - fib +]
                ifte .
            10 fib
        """)
        assert evaluator.stack.peek().value == 55

    def test_definition_with_combinator(self, evaluator):
        """Definition using combinators."""
        evaluator.run("DEFINE all-positive == [0 >] all . [1 2 3 4 5] all-positive")
        assert evaluator.stack.peek().value is True


class TestBackwardCompatibility:
    """Ensure backward compatibility with code without definitions."""

    def test_pure_program(self, evaluator):
        """Program without definitions still works."""
        evaluator.run("1 2 3 + +")
        assert evaluator.stack.peek().value == 6

    def test_semicolons_ignored(self, evaluator):
        """Semicolons outside definitions are ignored."""
        evaluator.run("1 ; 2 ; 3")
        assert evaluator.stack.depth == 3

    def test_periods_ignored(self, evaluator):
        """Periods outside definitions are ignored."""
        evaluator.run("1 . 2 . 3")
        assert evaluator.stack.depth == 3
