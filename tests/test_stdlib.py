"""
Tests for Phase 7 standard library.
"""

import pytest

from pyjoy.types import JoyType


class TestPhase7Primitives:
    """Tests for Phase 7 primitives."""

    def test_include_nonexistent(self, evaluator):
        """include raises error for nonexistent file."""
        with pytest.raises(Exception, match="file not found"):
            evaluator.run('"nonexistent_file_12345.joy" include')

    def test_body_user_defined(self, evaluator):
        """body returns quotation for user-defined word."""
        evaluator.run('DEFINE square == dup * . "square" intern body')
        result = evaluator.stack.peek()
        assert result.type == JoyType.QUOTATION
        assert len(result.value.terms) == 2  # dup and *

    def test_body_primitive(self, evaluator):
        """body returns empty quotation for primitives."""
        evaluator.run('"dup" intern body')
        result = evaluator.stack.peek()
        assert result.type == JoyType.QUOTATION
        assert len(result.value.terms) == 0

    def test_body_undefined(self, evaluator):
        """body returns empty quotation for undefined words."""
        evaluator.run('"undefined_word_12345" intern body')
        result = evaluator.stack.peek()
        assert result.type == JoyType.QUOTATION
        assert len(result.value.terms) == 0

    def test_chr(self, evaluator):
        """chr converts integer to character."""
        evaluator.run("65 chr")
        result = evaluator.stack.peek()
        assert result.type == JoyType.CHAR
        assert result.value == "A"

    def test_chr_newline(self, evaluator):
        """chr works for newline."""
        evaluator.run("10 chr")
        result = evaluator.stack.peek()
        assert result.type == JoyType.CHAR
        assert result.value == "\n"

    def test_drop_list(self, evaluator):
        """drop removes first N elements from list/quotation."""
        evaluator.run("[1 2 3 4 5] 2 drop")
        result = evaluator.stack.peek()
        assert result.type in (JoyType.LIST, JoyType.QUOTATION)
        items = result.value if result.type == JoyType.LIST else result.value.terms
        assert len(items) == 3
        assert items[0].value == 3

    def test_drop_string(self, evaluator):
        """drop removes first N characters from string."""
        evaluator.run('"hello" 2 drop')
        result = evaluator.stack.peek()
        assert result.type == JoyType.STRING
        assert result.value == "llo"

    def test_drop_empty(self, evaluator):
        """drop returns empty when N >= length."""
        evaluator.run("[1 2] 5 drop")
        result = evaluator.stack.peek()
        assert result.type in (JoyType.LIST, JoyType.QUOTATION)
        items = result.value if result.type == JoyType.LIST else result.value.terms
        assert len(items) == 0

    def test_localtime(self, evaluator):
        """localtime returns a list of time components."""
        evaluator.run("0 localtime")  # Epoch time
        result = evaluator.stack.peek()
        assert result.type == JoyType.LIST
        assert len(result.value) == 9
        # Year should be 1970 for epoch
        assert result.value[0].value == 1970

    def test_gmtime(self, evaluator):
        """gmtime returns UTC time list."""
        evaluator.run("0 gmtime")
        result = evaluator.stack.peek()
        assert result.type == JoyType.LIST
        assert len(result.value) == 9
        assert result.value[0].value == 1970  # Year
        assert result.value[1].value == 1  # Month (January)
        assert result.value[2].value == 1  # Day

    def test_maxint(self, evaluator):
        """maxint pushes maximum integer value."""
        import sys

        evaluator.run("maxint")
        result = evaluator.stack.peek()
        assert result.type == JoyType.INTEGER
        assert result.value == sys.maxsize

    def test_setautoput(self, evaluator):
        """setautoput is a no-op for compatibility."""
        evaluator.run("42 1 setautoput")
        # Should just pop the value, leaving 42
        assert evaluator.stack.depth == 1
        assert evaluator.stack.peek().value == 42

    def test_setundeferror(self, evaluator):
        """setundeferror is a no-op for compatibility."""
        evaluator.run("42 1 setundeferror")
        assert evaluator.stack.depth == 1
        assert evaluator.stack.peek().value == 42

    def test_rollupd(self, evaluator):
        """rollupd rolls up under top element."""
        evaluator.run("1 2 3 4 rollupd")
        # [1 2 3 4] -> [2 3 1 4]
        result = [evaluator.stack.pop().value for _ in range(4)]
        assert result == [4, 1, 3, 2]

    def test_rolldownd(self, evaluator):
        """rolldownd rolls down under top element."""
        evaluator.run("1 2 3 4 rolldownd")
        # [1 2 3 4] -> [3 1 2 4]
        result = [evaluator.stack.pop().value for _ in range(4)]
        assert result == [4, 2, 1, 3]


class TestHideInEnd:
    """Tests for HIDE/IN/END scoping."""

    def test_hide_basic(self, evaluator):
        """HIDE/IN/END parses and executes."""
        evaluator.run("""
            HIDE
                helper == 10
            IN
                use-helper == helper 2 *
            END.
            use-helper
        """)
        assert evaluator.stack.peek().value == 20

    def test_hide_hidden_visible_in_public(self, evaluator):
        """Hidden definitions are visible in public section."""
        evaluator.run("""
            HIDE
                secret == 42
            IN
                reveal == secret
            END.
            reveal
        """)
        assert evaluator.stack.peek().value == 42

    def test_hide_multiple_hidden(self, evaluator):
        """Multiple hidden definitions work."""
        evaluator.run("""
            HIDE
                a == 1;
                b == 2
            IN
                sum == a b +
            END.
            sum
        """)
        assert evaluator.stack.peek().value == 3


class TestStdlibDefinitions:
    """Tests for standard library style definitions."""

    def test_dup2_definition(self, evaluator):
        """dup2 == dupd dup swapd works."""
        evaluator.run("DEFINE dup2 == dupd dup swapd . 5 7 dup2")
        # [5 7] -> dup2 -> [5 7 5 7]
        result = [evaluator.stack.pop().value for _ in range(4)]
        assert result == [7, 5, 7, 5]

    def test_pop2_definition(self, evaluator):
        """pop2 == pop pop works."""
        evaluator.run("DEFINE pop2 == pop pop . 1 2 3 pop2")
        assert evaluator.stack.depth == 1
        assert evaluator.stack.peek().value == 1

    def test_newstack_definition(self, evaluator):
        """newstack == [] unstack clears stack."""
        evaluator.run("DEFINE newstack == [] unstack . 1 2 3 newstack")
        assert evaluator.stack.depth == 0

    def test_swoncat_definition(self, evaluator):
        """swoncat == swap concat works."""
        evaluator.run("DEFINE swoncat == swap concat . [1 2] [3 4] swoncat")
        result = evaluator.stack.peek()
        assert result.type == JoyType.LIST
        values = [v.value for v in result.value]
        assert values == [3, 4, 1, 2]

    def test_sequor_definition(self, evaluator):
        """sequor - sequential or works."""
        evaluator.run("DEFINE sequor == [pop true] swap ifte . 5 [0 >] [even] sequor")
        assert evaluator.stack.peek().value is True  # 5 > 0

    def test_dipd_builtin(self, evaluator):
        """Built-in dipd works correctly."""
        # dipd: X Y [P] -> P X Y (execute P, then restore X and Y)
        evaluator.run("1 2 3 4 [+] dipd")
        # Stack: [1 2 3 4 [+]]
        # dipd pops [+], 4, 3 -> executes [+] on [1 2] -> [3], then pushes 3, 4
        # Result: [3 3 4]
        result = [evaluator.stack.pop().value for _ in range(3)]
        assert result == [4, 3, 3]

    def test_conjoin_definition(self, evaluator):
        """conjoin creates AND combination of predicates."""
        evaluator.run("""
            DEFINE conjoin == [[false] ifte] cons cons .
            5 [0 >] [10 <] conjoin i
        """)
        assert evaluator.stack.peek().value is True

    def test_disjoin_definition(self, evaluator):
        """disjoin creates OR combination of predicates."""
        evaluator.run("""
            DEFINE disjoin == [ifte] cons [true] swons cons .
            15 [0 <] [10 >] disjoin i
        """)
        assert evaluator.stack.peek().value is True

    def test_negate_definition(self, evaluator):
        """negate inverts a predicate."""
        evaluator.run("""
            DEFINE negate == [[false] [true] ifte] cons .
            5 [0 >] negate i
        """)
        assert evaluator.stack.peek().value is False


class TestAggregateLibrary:
    """Tests for aggregate library definitions."""

    def test_unitlist(self, evaluator):
        """unitlist == [] cons works."""
        evaluator.run("DEFINE unitlist == [] cons . 42 unitlist")
        result = evaluator.stack.peek()
        assert result.type == JoyType.LIST
        assert len(result.value) == 1
        assert result.value[0].value == 42

    def test_pairlist(self, evaluator):
        """pairlist == [] cons cons works."""
        evaluator.run("DEFINE pairlist == [] cons cons . 1 2 pairlist")
        result = evaluator.stack.peek()
        assert result.type == JoyType.LIST
        assert len(result.value) == 2

    def test_second(self, evaluator):
        """second == rest first works."""
        evaluator.run("DEFINE second == rest first . [1 2 3] second")
        assert evaluator.stack.peek().value == 2

    def test_third(self, evaluator):
        """third == rest rest first works."""
        evaluator.run("DEFINE third == rest rest first . [1 2 3 4] third")
        assert evaluator.stack.peek().value == 3

    def test_shunt(self, evaluator):
        """shunt == [swons] step works."""
        evaluator.run("DEFINE shunt == [swons] step . [] [1 2 3] shunt")
        result = evaluator.stack.peek()
        assert result.type == JoyType.LIST
        values = [v.value for v in result.value]
        assert values == [3, 2, 1]

    def test_sum(self, evaluator):
        """sum == 0 [+] fold works."""
        evaluator.run("DEFINE sum == 0 [+] fold . [1 2 3 4 5] sum")
        assert evaluator.stack.peek().value == 15

    def test_zip_lists(self, evaluator):
        """zip pairs up elements from two lists."""
        evaluator.run("""
            DEFINE null2 == [null] dip null or .
            DEFINE pop2 == pop pop .
            DEFINE unconsd == [uncons] dip .
            DEFINE uncons2 == unconsd uncons swapd .
            DEFINE pairlist == [] cons cons .
            DEFINE zip == [null2] [pop2 []] [uncons2] [[pairlist] dip cons] linrec .
            [1 2 3] [4 5 6] zip
        """)
        result = evaluator.stack.peek()
        assert result.type == JoyType.LIST
        assert len(result.value) == 3


class TestNumericalLibrary:
    """Tests for numerical library definitions."""

    def test_positive(self, evaluator):
        """positive == 0 > works."""
        evaluator.run("DEFINE positive == 0 > . 5 positive")
        assert evaluator.stack.peek().value is True

        evaluator.run("-5 positive")
        assert evaluator.stack.peek().value is False

    def test_negative(self, evaluator):
        """negative == 0 < works."""
        evaluator.run("DEFINE negative == 0 < . -5 negative")
        assert evaluator.stack.peek().value is True

    def test_even(self, evaluator):
        """even == 2 rem null works."""
        evaluator.run("DEFINE even == 2 rem null . 4 even")
        assert evaluator.stack.peek().value is True

        evaluator.run("5 even")
        assert evaluator.stack.peek().value is False

    def test_odd(self, evaluator):
        """odd == even not works."""
        evaluator.run("DEFINE even == 2 rem null . DEFINE odd == even not . 5 odd")
        assert evaluator.stack.peek().value is True

    def test_fact_iterative(self, evaluator):
        """Iterative factorial using times."""
        evaluator.run("""
            DEFINE fact == [1 1] dip [dup [*] dip succ] times pop .
            5 fact
        """)
        assert evaluator.stack.peek().value == 120

    def test_gcd(self, evaluator):
        """GCD using while loop."""
        evaluator.run("""
            DEFINE gcd == [0 >] [dup rollup rem] while pop .
            48 18 gcd
        """)
        assert evaluator.stack.peek().value == 6

    def test_fahrenheit(self, evaluator):
        """fahrenheit == 9 * 5 / 32 + works."""
        evaluator.run("DEFINE fahrenheit == 9 * 5 / 32 + . 0 fahrenheit")
        assert evaluator.stack.peek().value == 32  # 0C = 32F

    def test_celsius(self, evaluator):
        """celsius == 32 - 5 * 9 / works."""
        evaluator.run("DEFINE celsius == 32 - 5 * 9 / . 32 celsius")
        assert evaluator.stack.peek().value == 0  # 32F = 0C
