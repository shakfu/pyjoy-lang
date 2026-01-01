"""
Tests for Phase 4 recursion combinators.
"""

from pyjoy.types import JoyType


class TestPrimrec:
    """Tests for primrec (primitive recursion)."""

    def test_primrec_factorial(self, evaluator):
        """primrec can compute factorial."""
        # 5! = 5 * 4 * 3 * 2 * 1 = 120
        evaluator.run("5 [1] [*] primrec")
        assert evaluator.stack.peek().value == 120

    def test_primrec_sum(self, evaluator):
        """primrec can compute sum of 1 to N."""
        # 1 + 2 + 3 + 4 + 5 = 15
        evaluator.run("5 [0] [+] primrec")
        assert evaluator.stack.peek().value == 15

    def test_primrec_zero(self, evaluator):
        """primrec with 0 just executes I."""
        evaluator.run("0 [42] [+] primrec")
        assert evaluator.stack.peek().value == 42

    def test_primrec_list(self, evaluator):
        """primrec on list combines with each member."""
        # Sum of [1 2 3 4 5] = 15
        evaluator.run("[1 2 3 4 5] [0] [+] primrec")
        assert evaluator.stack.peek().value == 15

    def test_primrec_product_list(self, evaluator):
        """primrec can compute product of list."""
        # Product of [1 2 3 4] = 24
        evaluator.run("[1 2 3 4] [1] [*] primrec")
        assert evaluator.stack.peek().value == 24


class TestLinrec:
    """Tests for linrec (linear recursion)."""

    def test_linrec_factorial(self, evaluator):
        """linrec can compute factorial."""
        # factorial = [0 =] [pop 1] [dup 1 -] [*] linrec
        evaluator.run("5 [0 =] [pop 1] [dup 1 -] [*] linrec")
        assert evaluator.stack.peek().value == 120

    def test_linrec_base_case(self, evaluator):
        """linrec handles base case directly."""
        evaluator.run("0 [0 =] [pop 1] [dup 1 -] [*] linrec")
        assert evaluator.stack.peek().value == 1

    def test_linrec_sum(self, evaluator):
        """linrec can compute sum."""
        # sum 1 to N: [0 <=] [pop 0] [dup pred] [+] linrec
        evaluator.run("5 [0 <=] [pop 0] [dup pred] [+] linrec")
        assert evaluator.stack.peek().value == 15

    def test_linrec_length(self, evaluator):
        """linrec can compute list length."""
        # length = [null] [pop 0] [rest] [succ] linrec
        evaluator.run("[1 2 3 4 5] [null] [pop 0] [rest] [succ] linrec")
        assert evaluator.stack.peek().value == 5


class TestBinrec:
    """Tests for binrec (binary recursion)."""

    def test_binrec_fibonacci(self, evaluator):
        """binrec can compute fibonacci."""
        # fib = [small] [] [pred dup pred] [+] binrec
        # small means value < 2 (i.e., 0 or 1)
        evaluator.run("10 [small] [] [pred dup pred] [+] binrec")
        assert evaluator.stack.peek().value == 55

    def test_binrec_base_case_0(self, evaluator):
        """binrec handles base case for 0."""
        evaluator.run("0 [small] [] [pred dup pred] [+] binrec")
        assert evaluator.stack.peek().value == 0

    def test_binrec_base_case_1(self, evaluator):
        """binrec handles base case for 1."""
        evaluator.run("1 [small] [] [pred dup pred] [+] binrec")
        assert evaluator.stack.peek().value == 1

    def test_binrec_fib_5(self, evaluator):
        """binrec computes fib(5) = 5."""
        evaluator.run("5 [small] [] [pred dup pred] [+] binrec")
        # fib(5) = 5
        assert evaluator.stack.peek().value == 5


class TestTailrec:
    """Tests for tailrec (tail recursion)."""

    def test_tailrec_countdown(self, evaluator):
        """tailrec can count up and collect values."""
        # Build list [9 8 7 6 5 4 3 2 1 0] from 0
        evaluator.run("[] 0 [dup 10 =] [pop] [dup [swons] dip succ] tailrec")
        result = evaluator.stack.peek()
        assert result.type in (JoyType.LIST, JoyType.QUOTATION)
        items = result.value if result.type == JoyType.LIST else result.value.terms
        assert len(items) == 10

    def test_tailrec_base_case(self, evaluator):
        """tailrec handles immediate base case."""
        evaluator.run("42 [true] [dup] [pop] tailrec")
        assert evaluator.stack.peek().value == 42

    def test_tailrec_sum_iterative(self, evaluator):
        """tailrec can compute sum iteratively."""
        # Sum 1 to 5: accumulator starts at 0, counter at 5
        evaluator.run("0 5 [dup 0 =] [pop] [dup rolldown + swap pred] tailrec")
        assert evaluator.stack.peek().value == 15

    def test_tailrec_gcd(self, evaluator):
        """tailrec can compute GCD."""
        # GCD using Euclidean algorithm
        # gcd(a, b) = if b = 0 then a else gcd(b, a mod b)
        evaluator.run("48 18 [dup 0 =] [pop] [dup rollup rem] tailrec")
        assert evaluator.stack.peek().value == 6


class TestGenrec:
    """Tests for genrec (general recursion)."""

    def test_genrec_factorial(self, evaluator):
        """genrec can compute factorial with explicit recursion."""
        # [null] [succ] [dup pred] [i *] genrec
        # R2 receives recursive quotation, executes it with i, then multiplies
        evaluator.run("5 [null] [succ] [dup pred] [i *] genrec")
        assert evaluator.stack.peek().value == 120

    def test_genrec_base_case(self, evaluator):
        """genrec handles base case."""
        evaluator.run("0 [null] [succ] [dup pred] [i *] genrec")
        assert evaluator.stack.peek().value == 1

    def test_genrec_fibonacci(self, evaluator):
        """genrec can compute fibonacci."""
        # [small] [] [pred dup pred] [app2 +] genrec
        evaluator.run("10 [small] [] [pred dup pred] [app2 +] genrec")
        assert evaluator.stack.peek().value == 55


class TestNullAndSmall:
    """Tests for null and small with various types."""

    def test_null_integer_zero(self, evaluator):
        """null returns true for zero."""
        evaluator.run("0 null")
        assert evaluator.stack.peek().value is True

    def test_null_integer_nonzero(self, evaluator):
        """null returns false for nonzero."""
        evaluator.run("5 null")
        assert evaluator.stack.peek().value is False

    def test_null_empty_list(self, evaluator):
        """null returns true for empty list."""
        evaluator.run("[] null")
        assert evaluator.stack.peek().value is True

    def test_small_integer_zero(self, evaluator):
        """small returns true for 0."""
        evaluator.run("0 small")
        assert evaluator.stack.peek().value is True

    def test_small_integer_one(self, evaluator):
        """small returns true for 1."""
        evaluator.run("1 small")
        assert evaluator.stack.peek().value is True

    def test_small_integer_two(self, evaluator):
        """small returns false for 2."""
        evaluator.run("2 small")
        assert evaluator.stack.peek().value is False

    def test_small_singleton_list(self, evaluator):
        """small returns true for singleton list."""
        evaluator.run("[1] small")
        assert evaluator.stack.peek().value is True


class TestRecursionExamples:
    """Complex examples using recursion combinators."""

    def test_factorial_primrec_linrec(self, evaluator):
        """primrec and linrec compute same factorial."""
        evaluator.run("5 [1] [*] primrec")
        primrec_result = evaluator.stack.pop().value

        evaluator.run("5 [0 =] [pop 1] [dup 1 -] [*] linrec")
        linrec_result = evaluator.stack.pop().value

        assert primrec_result == 120
        assert linrec_result == 120

    def test_fibonacci_binrec_genrec(self, evaluator):
        """binrec and genrec compute same fibonacci."""
        evaluator.run("8 [small] [] [pred dup pred] [+] binrec")
        binrec_result = evaluator.stack.pop().value

        evaluator.run("8 [small] [] [pred dup pred] [app2 +] genrec")
        genrec_result = evaluator.stack.pop().value

        # fib(8) = 21
        assert binrec_result == 21
        assert genrec_result == 21

    def test_sum_methods(self, evaluator):
        """Different methods compute same sum."""
        # Using primrec
        evaluator.run("5 [0] [+] primrec")
        primrec_sum = evaluator.stack.pop().value

        # Using linrec
        evaluator.run("5 [0 <=] [pop 0] [dup pred] [+] linrec")
        linrec_sum = evaluator.stack.pop().value

        # Using tailrec
        evaluator.run("0 5 [dup 0 =] [pop] [dup rolldown + swap pred] tailrec")
        tailrec_sum = evaluator.stack.pop().value

        assert primrec_sum == 15
        assert linrec_sum == 15
        assert tailrec_sum == 15
