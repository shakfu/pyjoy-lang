"""
Tests for Phase 3 combinators (higher-order operations).
"""

from pyjoy.types import JoyType


class TestExecutionCombinators:
    """Tests for execution combinators."""

    def test_x_combinator(self, evaluator):
        """x executes quotation without consuming it."""
        evaluator.run("[dup] x")
        # Quotation still on stack, and dup executed (pushing copy of quotation)
        assert evaluator.stack.depth == 2

    def test_dip(self, evaluator):
        """dip executes with top temporarily removed."""
        evaluator.run("1 2 [dup] dip")
        # Stack: 1 -> dup -> 1 1, then restore 2
        # Result: 1 1 2
        assert evaluator.stack.depth == 3
        assert evaluator.stack.peek(0).value == 2
        assert evaluator.stack.peek(1).value == 1
        assert evaluator.stack.peek(2).value == 1

    def test_dipd(self, evaluator):
        """dipd executes with top two temporarily removed."""
        evaluator.run("1 2 3 [dup] dipd")
        # Stack: 1 -> dup -> 1 1, then restore 2 3
        # Result: 1 1 2 3
        assert evaluator.stack.depth == 4
        assert evaluator.stack.peek(0).value == 3
        assert evaluator.stack.peek(1).value == 2

    def test_keep(self, evaluator):
        """keep executes P and restores X."""
        evaluator.run("5 [dup *] keep")
        # 5 dup * = 25, then restore 5
        # Result: 25 5
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == 5
        assert evaluator.stack.peek(1).value == 25

    def test_nullary(self, evaluator):
        """nullary saves result, restores stack."""
        evaluator.run("1 2 3 [+] nullary")
        # Stack preserved as 1 2 3, result of 2+3=5 pushed
        # But wait, nullary pops quotation first, then executes on remaining stack
        # Actually: 1 2 3 [+] -> pop quot -> 1 2 3 -> execute + -> 1 5 -> pop result=5
        # -> restore to 1 2 3 -> push 5
        # Result: 1 2 3 5
        assert evaluator.stack.depth == 4
        assert evaluator.stack.peek(0).value == 5

    def test_unary(self, evaluator):
        """unary applies P to X, restores stack, pushes result."""
        evaluator.run("10 5 [dup *] unary")
        # 10 5 [dup *] -> pop quot, pop 5 -> save stack (10)
        # push 5, execute dup * = 25 -> pop result
        # restore stack (10) -> push 25
        # Result: 10 25
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == 25
        assert evaluator.stack.peek(1).value == 10

    def test_binary(self, evaluator):
        """binary applies P to X Y, restores stack, pushes result."""
        evaluator.run("100 3 4 [+] binary")
        # Save stack (100), push 3 4, execute + = 7
        # Restore (100), push 7
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == 7
        assert evaluator.stack.peek(1).value == 100


class TestConditionalCombinators:
    """Tests for conditional combinators."""

    def test_ifte_true(self, evaluator):
        """ifte executes then-branch when condition is true."""
        evaluator.run("5 [0 >] [dup *] [neg] ifte")
        # 5 > 0 is true, so dup * = 25
        assert evaluator.stack.peek().value == 25

    def test_ifte_false(self, evaluator):
        """ifte executes else-branch when condition is false."""
        evaluator.run("-5 [0 >] [dup *] [neg] ifte")
        # -5 > 0 is false, so neg = 5
        assert evaluator.stack.peek().value == 5

    def test_ifte_preserves_stack(self, evaluator):
        """ifte restores stack before executing branch."""
        evaluator.run("10 [pop true] [dup] [pop] ifte")
        # Condition pops 10 and pushes true
        # Stack restored to 10 before executing [dup]
        # Result: 10 10
        assert evaluator.stack.depth == 2

    def test_branch_true(self, evaluator):
        """branch executes then-branch when B is true."""
        evaluator.run("5 true [dup *] [neg] branch")
        assert evaluator.stack.peek().value == 25

    def test_branch_false(self, evaluator):
        """branch executes else-branch when B is false."""
        evaluator.run("5 false [dup *] [neg] branch")
        assert evaluator.stack.peek().value == -5


class TestIterationCombinators:
    """Tests for iteration combinators."""

    def test_step(self, evaluator):
        """step executes P for each element."""
        evaluator.run("0 [1 2 3] [+] step")
        # 0 + 1 + 2 + 3 = 6
        assert evaluator.stack.peek().value == 6

    def test_map(self, evaluator):
        """map transforms each element."""
        evaluator.run("[1 2 3] [dup *] map")
        result = evaluator.stack.peek()
        assert result.type == JoyType.LIST
        assert result.value[0].value == 1
        assert result.value[1].value == 4
        assert result.value[2].value == 9

    def test_map_preserves_stack(self, evaluator):
        """map doesn't affect stack below aggregate."""
        evaluator.run("100 [1 2 3] [succ] map")
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(1).value == 100

    def test_filter(self, evaluator):
        """filter keeps elements where P is true."""
        evaluator.run("[1 2 3 4 5 6] [2 rem 0 =] filter")
        # Keep even numbers
        result = evaluator.stack.peek()
        assert len(result.value) == 3
        assert result.value[0].value == 2
        assert result.value[1].value == 4
        assert result.value[2].value == 6

    def test_fold(self, evaluator):
        """fold reduces aggregate with binary operation."""
        evaluator.run("[1 2 3 4] 0 [+] fold")
        # 0 + 1 + 2 + 3 + 4 = 10
        assert evaluator.stack.peek().value == 10

    def test_fold_product(self, evaluator):
        """fold can compute product."""
        evaluator.run("[1 2 3 4] 1 [*] fold")
        # 1 * 1 * 2 * 3 * 4 = 24
        assert evaluator.stack.peek().value == 24

    def test_each(self, evaluator):
        """each is alias for step."""
        evaluator.run("0 [1 2 3] [+] each")
        assert evaluator.stack.peek().value == 6

    def test_any_true(self, evaluator):
        """any returns true if any element satisfies P."""
        evaluator.run("[1 2 3 4] [2 =] any")
        assert evaluator.stack.peek().value is True

    def test_any_false(self, evaluator):
        """any returns false if no element satisfies P."""
        evaluator.run("[1 2 3 4] [10 =] any")
        assert evaluator.stack.peek().value is False

    def test_all_true(self, evaluator):
        """all returns true if all elements satisfy P."""
        evaluator.run("[2 4 6 8] [2 rem 0 =] all")
        # All are even
        assert evaluator.stack.peek().value is True

    def test_all_false(self, evaluator):
        """all returns false if any element fails P."""
        evaluator.run("[2 4 5 8] [2 rem 0 =] all")
        # 5 is odd
        assert evaluator.stack.peek().value is False


class TestLoopingCombinators:
    """Tests for looping combinators."""

    def test_times(self, evaluator):
        """times executes P exactly N times."""
        evaluator.run("1 5 [2 *] times")
        # 1 * 2^5 = 32
        assert evaluator.stack.peek().value == 32

    def test_times_zero(self, evaluator):
        """times with 0 does nothing."""
        evaluator.run("42 0 [pop 0] times")
        assert evaluator.stack.peek().value == 42

    def test_while(self, evaluator):
        """while loops until condition is false."""
        evaluator.run("1 [dup 10 <] [2 *] while")
        # 1 -> 2 -> 4 -> 8 -> 16 (stops because 16 >= 10)
        assert evaluator.stack.peek().value == 16

    def test_loop(self, evaluator):
        """loop executes until P returns false."""
        # loop pops result each iteration, so P must both do work and return bool
        # Count down: starts at 3, runs while dup 0 > is true
        # When value hits 0: 0 dup = 0 0, 0 > = false, but [pred] dip already ran = -1
        # Final state: -1 false, pop false (stop), stack has -1
        evaluator.run("3 [dup 0 > [pred] dip] loop")
        assert evaluator.stack.peek().value == -1

    def test_while_countdown(self, evaluator):
        """while can count down."""
        evaluator.run("0 5 [dup 0 >] [dup rolldown + swap pred] while pop")
        # Sum 5+4+3+2+1 = 15
        assert evaluator.stack.peek().value == 15


class TestAdditionalCombinators:
    """Tests for bi, tri, cleave, etc."""

    def test_bi(self, evaluator):
        """bi applies two quotations to same value."""
        evaluator.run("5 [dup *] [succ] bi")
        # 5 dup * = 25, 5 succ = 6
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == 6
        assert evaluator.stack.peek(1).value == 25

    def test_tri(self, evaluator):
        """tri applies three quotations to same value."""
        evaluator.run("10 [pred] [dup] [succ] tri")
        # 10 pred = 9, 10 dup = 10 10, 10 succ = 11
        # Actually tri doesn't preserve intermediate results properly
        # Let me check the semantics again
        # tri: X [P] [Q] [R] -> execute P on X, then Q on X, then R on X
        # Results left on stack in order
        assert evaluator.stack.depth == 4  # 9, 10, 10, 11

    def test_compose(self, evaluator):
        """compose combines two quotations."""
        evaluator.run("[1 +] [2 *] compose")
        result = evaluator.stack.peek()
        assert result.type == JoyType.QUOTATION
        # The composed quotation should have terms from both

    def test_compose_execute(self, evaluator):
        """composed quotation works correctly."""
        evaluator.run("5 [1 +] [2 *] compose i")
        # (5 + 1) * 2 = 12
        assert evaluator.stack.peek().value == 12

    def test_app1(self, evaluator):
        """app1 applies P to X."""
        evaluator.run("5 [dup *] app1")
        assert evaluator.stack.peek().value == 25

    def test_app2(self, evaluator):
        """app2 applies P to X and Y separately."""
        evaluator.run("3 4 [dup *] app2")
        # 3 -> 9, 4 -> 16
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == 16
        assert evaluator.stack.peek(1).value == 9

    def test_infra(self, evaluator):
        """infra executes P with list as stack."""
        evaluator.run("[1 2 3] [+ +] infra")
        # Stack becomes 1 2 3, execute + + = 6
        # Result is [6]
        result = evaluator.stack.peek()
        assert result.type == JoyType.LIST
        assert result.value[0].value == 6


class TestComplexCombinatorExpressions:
    """Tests for complex expressions using combinators."""

    def test_factorial_with_ifte(self, evaluator):
        """Factorial using ifte (non-recursive for now)."""
        # 5! using fold
        evaluator.run("[1 2 3 4 5] 1 [*] fold")
        assert evaluator.stack.peek().value == 120

    def test_sum_of_squares(self, evaluator):
        """Sum of squares using map and fold."""
        evaluator.run("[1 2 3 4] [dup *] map 0 [+] fold")
        # 1 + 4 + 9 + 16 = 30
        assert evaluator.stack.peek().value == 30

    def test_filter_and_sum(self, evaluator):
        """Filter then sum."""
        evaluator.run("[1 2 3 4 5 6] [2 rem 0 =] filter 0 [+] fold")
        # Sum of evens: 2 + 4 + 6 = 12
        assert evaluator.stack.peek().value == 12

    def test_map_filter_fold(self, evaluator):
        """Chain of map, filter, fold."""
        evaluator.run("[1 2 3 4 5] [dup *] map [10 <] filter 0 [+] fold")
        # Squares: 1 4 9 16 25
        # Filter < 10: 1 4 9
        # Sum: 14
        assert evaluator.stack.peek().value == 14

    def test_nested_ifte(self, evaluator):
        """Nested conditional."""
        evaluator.run("15 [10 <] [1] [[20 <] [2] [3] ifte] ifte")
        # 15 >= 10, so check second condition
        # 15 < 20, so result is 2
        assert evaluator.stack.peek().value == 2

    def test_power_of_two(self, evaluator):
        """Compute 2^5 using while loop."""
        # Iterative: start with 1, multiply by 2 while n > 0
        evaluator.run("1 5 [dup 0 >] [[2 *] dip pred] while pop")
        # 1 * 2^5 = 32
        assert evaluator.stack.peek().value == 32

    def test_dip_usage(self, evaluator):
        """Practical use of dip."""
        # Add to second element: 1 2 3 -> 1 (2+10) 3
        evaluator.run("1 2 3 [10 +] dip")
        # 3 removed, 2+10=12, restore 3
        assert evaluator.stack.peek(0).value == 3
        assert evaluator.stack.peek(1).value == 12
        assert evaluator.stack.peek(2).value == 1


class TestCondCombinator:
    """Tests for cond combinator - matching cond.joy test file."""

    def test_cond_first_match(self, evaluator):
        """cond selects first matching clause."""
        evaluator.run("""
            DEFINE test == [[[dup 1 =] "one"]
                            [[dup 2 =] "two"]
                            ["other"]] cond.
            1 test
        """)
        # Stack should be: 1, "one"
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == "one"
        assert evaluator.stack.peek(1).value == 1

    def test_cond_second_match(self, evaluator):
        """cond selects second clause when first doesn't match."""
        evaluator.run("""
            DEFINE test == [[[dup 1 =] "one"]
                            [[dup 2 =] "two"]
                            ["other"]] cond.
            2 test
        """)
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == "two"
        assert evaluator.stack.peek(1).value == 2

    def test_cond_default(self, evaluator):
        """cond uses default clause when no condition matches."""
        evaluator.run("""
            DEFINE test == [[[dup 1 =] "one"]
                            [[dup 2 =] "two"]
                            ["other"]] cond.
            3 test
        """)
        assert evaluator.stack.depth == 2
        assert evaluator.stack.peek(0).value == "other"
        assert evaluator.stack.peek(1).value == 3

    def test_cond_stack_equal(self, evaluator):
        """cond result matches expected with equal."""
        evaluator.run("""
            DEFINE test == [[[dup 1 =] "one"]
                            [[dup 2 =] "two"]
                            ["other"]] cond.
            1 test stack ["one" 1] equal
        """)
        assert evaluator.stack.peek().value is True

    def test_cond_single_default(self, evaluator):
        """cond with only default clause."""
        evaluator.run("""
            DEFINE test == [["other"]] cond.
            1 test
        """)
        assert evaluator.stack.peek().value == "other"

    def test_cond_empty_clause(self, evaluator):
        """cond with empty clause does nothing."""
        evaluator.run("""
            DEFINE test == [[]] cond.
            1 test
        """)
        assert evaluator.stack.peek().value == 1


class TestCondWithStdlib:
    """Tests for cond with stdlib loaded - matches cond.joy file."""

    def test_cond_file_exact(self, evaluator_with_stdlib):
        """Test exact content from cond.joy file."""
        # This matches the exact structure in cond.joy
        evaluator_with_stdlib.run("""
DEFINE\ttest == [[[dup 1 =] "one"]
\t\t [[dup 2 =] "two"]
\t\t ["other"]] cond.

1 test stack ["one" 1] equal
        """)
        assert evaluator_with_stdlib.stack.peek().value is True

    def test_cond_with_unstack(self, evaluator_with_stdlib):
        """Test cond followed by unstack and more tests."""
        evaluator_with_stdlib.run("""
DEFINE\ttest == [[[dup 1 =] "one"]
\t\t [[dup 2 =] "two"]
\t\t ["other"]] cond.

1 test stack ["one" 1] equal
        """)
        first_result = evaluator_with_stdlib.stack.pop().value

        evaluator_with_stdlib.run("[] unstack")
        evaluator_with_stdlib.run('2 test stack ["two" 2] equal')
        second_result = evaluator_with_stdlib.stack.pop().value

        evaluator_with_stdlib.run("[] unstack")
        evaluator_with_stdlib.run('3 test stack ["other" 3] equal')
        third_result = evaluator_with_stdlib.stack.pop().value

        assert first_result is True
        assert second_result is True
        assert third_result is True

    def test_cond_full_file(self, evaluator_with_stdlib):
        """Test the exact full cond.joy file content."""
        import io
        import sys
        from pathlib import Path

        # Read the actual file
        filepath = Path("tests/joy/cond.joy")
        source = filepath.read_text()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        evaluator_with_stdlib.run(source)

        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        # Check output - should be all "true"
        lines = [ln.strip() for ln in output.strip().split("\n") if ln.strip()]
        assert all(ln == "true" for ln in lines), f"Expected all true, got: {lines}"

    def test_cond_with_inline_redefine(self, evaluator_with_stdlib):
        """Test that definitions are processed inline, not all upfront.

        This is a regression test for the bug where all DEFINEs were registered
        before any code executed, causing the last DEFINE to be active throughout.
        """
        import io
        import sys

        source = '''DEFINE test == [[[dup 1 =] "one"]
         [[dup 2 =] "two"]
         ["other"]] cond.

1 test stack ["one" 1] equal.
[] unstack.

DEFINE test == [["other"]] cond.

1 test "other" =.
'''
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        evaluator_with_stdlib.run(source)
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        lines = [ln.strip() for ln in output.strip().split("\n") if ln.strip()]
        assert lines == ["true", "true"], f"Expected ['true', 'true'], got: {lines}"
