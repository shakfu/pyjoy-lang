"""
pyjoy.evaluator.combinators - Higher-order combinators.

Contains: i, x, dip, dipd, dipdd, keep, nullary, unary, binary, ternary,
ifte, branch, cond, step, map, filter, fold, each, any, all, some, split,
times, while, loop, bi, tri, cleave, spread, infra, app1-4, compose,
primrec, linrec, binrec, tailrec, genrec, condlinrec, condnestrec, construct,
unary2, unary3, unary4, opcase, treestep, treerec, treegenrec
"""

from __future__ import annotations

from pyjoy.errors import JoyTypeError
from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyQuotation, JoyType, JoyValue

from .core import expect_quotation, joy_word


def _term_to_value(term) -> JoyValue:
    """Convert a quotation term to a JoyValue."""
    if isinstance(term, JoyValue):
        return term
    elif isinstance(term, str):
        return JoyValue.symbol(term)
    elif isinstance(term, JoyQuotation):
        return JoyValue.quotation(term)
    elif isinstance(term, int):
        return JoyValue.integer(term)
    elif isinstance(term, float):
        return JoyValue.floating(term)
    elif isinstance(term, bool):
        return JoyValue.boolean(term)
    else:
        return JoyValue.symbol(str(term))


def _get_aggregate(v: JoyValue, op: str) -> tuple:
    """Extract aggregate contents as tuple (raw terms for quotations)."""
    if v.type == JoyType.LIST:
        return v.value
    elif v.type == JoyType.QUOTATION:
        # Return raw terms - do NOT convert to JoyValues here
        return v.value.terms
    elif v.type == JoyType.STRING:
        return tuple(JoyValue.char(c) for c in v.value)
    elif v.type == JoyType.SET:
        return tuple(JoyValue.integer(x) for x in sorted(v.value))
    else:
        raise JoyTypeError(op, "aggregate", v.type.name)


def _make_aggregate(items: tuple, original_type: JoyType) -> JoyValue:
    """Create aggregate from items, matching original type.

    Preserves STRING and SET types. QUOTATION and LIST both return LIST
    since they're interchangeable in most Joy contexts.
    """
    if original_type == JoyType.STRING:
        try:
            # Accept both CHAR and INTEGER (C treats chars as ints)
            chars = []
            for v in items:
                if v.type == JoyType.CHAR:
                    chars.append(v.value)
                elif v.type == JoyType.INTEGER:
                    chars.append(chr(v.value))
            return JoyValue.string("".join(chars))
        except (AttributeError, TypeError, ValueError):
            return JoyValue.list(items)
    elif original_type == JoyType.SET:
        try:
            members = frozenset(v.value for v in items if v.type == JoyType.INTEGER)
            return JoyValue.joy_set(members)
        except Exception:
            return JoyValue.list(items)
    else:
        # QUOTATION and LIST both return LIST
        return JoyValue.list(items)


def _ensure_joy_value(item) -> JoyValue:
    """Ensure item is a JoyValue (convert raw quotation terms if needed)."""
    if isinstance(item, JoyValue):
        return item
    return _term_to_value(item)


# -----------------------------------------------------------------------------
# Basic Execution Combinators
# -----------------------------------------------------------------------------


@joy_word(name="i", params=1, doc="[P] -> ...")
def i_combinator(ctx: ExecutionContext) -> None:
    """Execute quotation or list."""
    quot = ctx.stack.pop()
    if quot.type == JoyType.QUOTATION:
        ctx.evaluator.execute(quot.value)
    elif quot.type == JoyType.LIST:
        for term in quot.value:
            ctx.evaluator._execute_term(term)
    else:
        raise JoyTypeError("i", "QUOTATION", quot.type.name)


@joy_word(name="x", params=1, doc="[P] -> ... [P]")
def x_combinator(ctx: ExecutionContext) -> None:
    """Execute quotation without consuming it."""
    quot = ctx.stack.peek()
    q = expect_quotation(quot, "x")
    ctx.evaluator.execute(q)


@joy_word(name="dip", params=2, doc="X [P] -> ... X")
def dip(ctx: ExecutionContext) -> None:
    """Execute P with X temporarily removed, then restore X."""
    quot, x = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "dip")
    ctx.evaluator.execute(q)
    ctx.stack.push_value(x)


@joy_word(name="dipd", params=3, doc="X Y [P] -> ... X Y")
def dipd(ctx: ExecutionContext) -> None:
    """Execute P with X and Y temporarily removed."""
    quot, y, x = ctx.stack.pop_n(3)
    q = expect_quotation(quot, "dipd")
    ctx.evaluator.execute(q)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)


@joy_word(name="dipdd", params=4, doc="X Y Z [P] -> ... X Y Z")
def dipdd(ctx: ExecutionContext) -> None:
    """Execute P with X, Y, Z temporarily removed."""
    quot, z, y, x = ctx.stack.pop_n(4)
    q = expect_quotation(quot, "dipdd")
    ctx.evaluator.execute(q)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)
    ctx.stack.push_value(z)


@joy_word(name="keep", params=2, doc="X [P] -> ... X")
def keep(ctx: ExecutionContext) -> None:
    """Execute P on X, then restore X."""
    quot, x = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "keep")
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)
    ctx.stack.push_value(x)


# -----------------------------------------------------------------------------
# Arity Combinators
# -----------------------------------------------------------------------------


@joy_word(name="nullary", params=1, doc="[P] -> X")
def nullary(ctx: ExecutionContext) -> None:
    """Execute P, save result, restore original stack, push result."""
    quot = ctx.stack.pop()
    q = expect_quotation(quot, "nullary")
    saved = ctx.stack._items.copy()
    ctx.evaluator.execute(q)
    result = ctx.stack.pop()
    ctx.stack._items = saved
    ctx.stack.push_value(result)


@joy_word(name="unary", params=2, doc="X [P] -> R")
def unary(ctx: ExecutionContext) -> None:
    """Execute P on X, save result, restore stack below X, push result."""
    quot, x = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "unary")
    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)
    result = ctx.stack.pop()
    ctx.stack._items = saved
    ctx.stack.push_value(result)


@joy_word(name="unary2", params=3, doc="X1 X2 [P] -> R1 R2")
def unary2(ctx: ExecutionContext) -> None:
    """Apply P to X1 and X2 separately."""
    quot, x2, x1 = ctx.stack.pop_n(3)
    q = expect_quotation(quot, "unary2")

    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x1)
    ctx.evaluator.execute(q)
    r1 = ctx.stack.pop()
    ctx.stack._items = saved

    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x2)
    ctx.evaluator.execute(q)
    r2 = ctx.stack.pop()
    ctx.stack._items = saved

    ctx.stack.push_value(r1)
    ctx.stack.push_value(r2)


@joy_word(name="unary3", params=4, doc="X1 X2 X3 [P] -> R1 R2 R3")
def unary3(ctx: ExecutionContext) -> None:
    """Apply P to X1, X2, X3 separately."""
    quot, x3, x2, x1 = ctx.stack.pop_n(4)
    q = expect_quotation(quot, "unary3")

    results = []
    for x in [x1, x2, x3]:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(x)
        ctx.evaluator.execute(q)
        results.append(ctx.stack.pop())
        ctx.stack._items = saved

    for r in results:
        ctx.stack.push_value(r)


@joy_word(name="unary4", params=5, doc="X1 X2 X3 X4 [P] -> R1 R2 R3 R4")
def unary4(ctx: ExecutionContext) -> None:
    """Apply P to X1, X2, X3, X4 separately."""
    quot, x4, x3, x2, x1 = ctx.stack.pop_n(5)
    q = expect_quotation(quot, "unary4")

    results = []
    for x in [x1, x2, x3, x4]:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(x)
        ctx.evaluator.execute(q)
        results.append(ctx.stack.pop())
        ctx.stack._items = saved

    for r in results:
        ctx.stack.push_value(r)


@joy_word(name="binary", params=3, doc="X Y [P] -> R")
def binary(ctx: ExecutionContext) -> None:
    """Execute P on X and Y, save result, restore stack, push result."""
    quot, y, x = ctx.stack.pop_n(3)
    q = expect_quotation(quot, "binary")
    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)
    ctx.evaluator.execute(q)
    result = ctx.stack.pop()
    ctx.stack._items = saved
    ctx.stack.push_value(result)


@joy_word(name="ternary", params=4, doc="X Y Z [P] -> R")
def ternary(ctx: ExecutionContext) -> None:
    """Execute P on X, Y, Z, save result, restore stack, push result."""
    quot, z, y, x = ctx.stack.pop_n(4)
    q = expect_quotation(quot, "ternary")
    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)
    ctx.stack.push_value(z)
    ctx.evaluator.execute(q)
    result = ctx.stack.pop()
    ctx.stack._items = saved
    ctx.stack.push_value(result)


# -----------------------------------------------------------------------------
# Conditional Combinators
# -----------------------------------------------------------------------------


@joy_word(name="ifte", params=3, doc="[B] [T] [F] -> ...")
def ifte(ctx: ExecutionContext) -> None:
    """If-then-else: execute B, if true execute T, else execute F."""
    f_quot, t_quot, b_quot = ctx.stack.pop_n(3)
    b = expect_quotation(b_quot, "ifte")
    t = expect_quotation(t_quot, "ifte")
    f = expect_quotation(f_quot, "ifte")

    saved = ctx.stack._items.copy()
    ctx.evaluator.execute(b)
    test_result = ctx.stack.pop()
    ctx.stack._items = saved

    if test_result.is_truthy():
        ctx.evaluator.execute(t)
    else:
        ctx.evaluator.execute(f)


@joy_word(name="branch", params=3, doc="B [T] [F] -> ...")
def branch(ctx: ExecutionContext) -> None:
    """If B is true execute T, else execute F."""
    f_quot, t_quot, b = ctx.stack.pop_n(3)
    t = expect_quotation(t_quot, "branch")
    f = expect_quotation(f_quot, "branch")

    if b.is_truthy():
        ctx.evaluator.execute(t)
    else:
        ctx.evaluator.execute(f)


@joy_word(name="cond", params=1, doc="[[B1 T1] [B2 T2] ... [D]] -> ...")
def cond(ctx: ExecutionContext) -> None:
    """Multi-way conditional. Each clause is [condition body]."""
    clauses = ctx.stack.pop()
    clause_list = _get_aggregate(clauses, "cond")

    if not clause_list:
        return

    saved = ctx.stack._items.copy()

    for clause in clause_list:
        # Clause can be a JoyValue(QUOTATION) or a raw JoyQuotation
        if isinstance(clause, JoyValue) and clause.type == JoyType.QUOTATION:
            clause_terms = clause.value.terms
        elif isinstance(clause, JoyQuotation):
            clause_terms = clause.terms
        else:
            raise JoyTypeError("cond", "QUOTATION clause", type(clause).__name__)
        if len(clause_terms) < 1:
            continue

        # Last clause might be default (single element)
        if len(clause_terms) == 1:
            ctx.stack._items = saved.copy()
            term = clause_terms[0]
            if isinstance(term, JoyQuotation):
                ctx.evaluator.execute(term)
            elif isinstance(term, JoyValue) and term.type == JoyType.QUOTATION:
                ctx.evaluator.execute(term.value)
            elif isinstance(term, JoyValue):
                # Literal value - push it
                ctx.stack.push_value(term)
            elif isinstance(term, str):
                ctx.evaluator._execute_symbol(term)
            return

        condition = clause_terms[0]
        body = clause_terms[1] if len(clause_terms) > 1 else None

        ctx.stack._items = saved.copy()
        if isinstance(condition, JoyQuotation):
            ctx.evaluator.execute(condition)
        elif isinstance(condition, JoyValue) and condition.type == JoyType.QUOTATION:
            ctx.evaluator.execute(condition.value)
        elif isinstance(condition, str):
            ctx.evaluator._execute_symbol(condition)
        else:
            ctx.stack.push_value(condition)

        test_result = ctx.stack.pop()

        if test_result.is_truthy():
            ctx.stack._items = saved.copy()
            if body is not None:
                if isinstance(body, JoyQuotation):
                    ctx.evaluator.execute(body)
                elif isinstance(body, JoyValue) and body.type == JoyType.QUOTATION:
                    ctx.evaluator.execute(body.value)
                elif isinstance(body, JoyValue):
                    # Literal value - push it
                    ctx.stack.push_value(body)
                elif isinstance(body, str):
                    ctx.evaluator._execute_symbol(body)
            return

    ctx.stack._items = saved


@joy_word(name="case", params=2, doc="X [[V1 B1] [V2 B2] ... [D]] -> ...")
def case(ctx: ExecutionContext) -> None:
    """Case dispatch based on value of X.

    Each clause is [value body...]. If X equals value, execute body (X is consumed).
    Last clause is the default case (X is preserved, entire clause is body).
    """
    cases, x = ctx.stack.pop_n(2)
    case_list = _get_aggregate(cases, "case")

    if not case_list:
        return

    # Process all clauses except the last (which is default)
    for i, case_clause in enumerate(case_list[:-1]):
        # Handle both JoyValue(QUOTATION) and raw JoyQuotation
        if isinstance(case_clause, JoyValue) and case_clause.type == JoyType.QUOTATION:
            case_terms = case_clause.value.terms
        elif isinstance(case_clause, JoyQuotation):
            case_terms = case_clause.terms
        else:
            continue

        if len(case_terms) < 2:
            continue

        # [value body...] clause
        value = case_terms[0]
        body = case_terms[1:]  # Rest is the body

        # Compare x with value
        match = False
        if isinstance(value, JoyValue):
            if x.type == value.type and x.value == value.value:
                match = True
            elif x.is_numeric() and value.is_numeric():
                match = x.value == value.value
        elif isinstance(value, (int, float)):
            if x.is_numeric():
                match = x.value == value

        if match:
            # For matched cases, X is consumed (not pushed back)
            ctx.evaluator.execute(JoyQuotation(tuple(body)))
            return

    # Default case (last clause) - X is preserved, execute entire clause as body
    default_clause = case_list[-1]
    is_joy_quot = (
        isinstance(default_clause, JoyValue)
        and default_clause.type == JoyType.QUOTATION
    )
    if is_joy_quot:
        default_body = default_clause.value.terms
    elif isinstance(default_clause, JoyQuotation):
        default_body = default_clause.terms
    else:
        return

    ctx.stack.push_value(x)
    ctx.evaluator.execute(JoyQuotation(tuple(default_body)))


@joy_word(name="opcase", params=2, doc="X [..[X Xs]..] -> [Xs]")
def opcase(ctx: ExecutionContext) -> None:
    """Indexing on type of X, returns matching case body as list."""
    cases, x = ctx.stack.pop_n(2)
    case_list = _get_aggregate(cases, "opcase")

    def types_match(pattern, value: JoyValue) -> bool:
        """Check if pattern matches value by type (and value for symbols)."""
        if isinstance(pattern, JoyValue):
            if pattern.type != value.type:
                return False
            # For symbols, also check the value matches
            if pattern.type == JoyType.SYMBOL:
                return pattern.value == value.value
            return True
        elif isinstance(pattern, str):
            # Pattern is a symbol name
            if value.type != JoyType.SYMBOL:
                return False
            return pattern == value.value
        return False

    def get_case_terms(case):
        """Extract terms from a case (handles both JoyValue and JoyQuotation)."""
        if isinstance(case, JoyValue) and case.type == JoyType.QUOTATION:
            return case.value.terms
        elif isinstance(case, JoyQuotation):
            return case.terms
        return None

    # Iterate through cases (except last which is default)
    for i, case in enumerate(case_list):
        case_terms = get_case_terms(case)
        if case_terms is None:
            continue

        is_last = i == len(case_list) - 1

        if is_last:
            # Last case is default - return entire case as list
            ctx.stack.push_value(
                JoyValue.list(tuple(_term_to_value(t) for t in case_terms))
            )
            return

        if len(case_terms) < 1:
            continue

        pattern = case_terms[0]
        body = case_terms[1:]

        if types_match(pattern, x):
            # Match found - return body as list
            ctx.stack.push_value(JoyValue.list(tuple(_term_to_value(t) for t in body)))
            return

    # No match and no default - push empty list
    ctx.stack.push_value(JoyValue.list(()))


# -----------------------------------------------------------------------------
# Iteration Combinators
# -----------------------------------------------------------------------------


@joy_word(name="step", params=2, doc="A [P] -> ...")
def step(ctx: ExecutionContext) -> None:
    """Execute P for each element of A, pushing element before each call."""
    quot, agg = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "step")
    items = _get_aggregate(agg, "step")

    for item in items:
        ctx.stack.push_value(_ensure_joy_value(item))
        ctx.evaluator.execute(q)


@joy_word(name="map", params=2, doc="A [P] -> A'")
def map_combinator(ctx: ExecutionContext) -> None:
    """Apply P to each element of A, collecting results."""
    quot, agg = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "map")
    items = _get_aggregate(agg, "map")
    original_type = agg.type

    results = []
    for item in items:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(_ensure_joy_value(item))
        ctx.evaluator.execute(q)
        result = ctx.stack.pop()
        results.append(result)
        ctx.stack._items = saved

    # Preserve original type (STRING, SET, LIST, QUOTATION)
    ctx.stack.push_value(_make_aggregate(tuple(results), original_type))


@joy_word(name="filter", params=2, doc="A [P] -> A'")
def filter_combinator(ctx: ExecutionContext) -> None:
    """Keep elements of A for which P returns true."""
    quot, agg = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "filter")
    items = _get_aggregate(agg, "filter")

    results = []
    for item in items:
        saved = ctx.stack._items.copy()
        joy_item = _ensure_joy_value(item)
        ctx.stack.push_value(joy_item)
        ctx.evaluator.execute(q)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if test_result.is_truthy():
            results.append(joy_item)

    # Preserve original aggregate type
    ctx.stack.push_value(_make_aggregate(tuple(results), agg.type))


@joy_word(name="split", params=2, doc="A [P] -> A1 A2")
def split(ctx: ExecutionContext) -> None:
    """Split A into elements satisfying P and those not."""
    quot, agg = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "split")
    items = _get_aggregate(agg, "split")

    satisfies = []
    not_satisfies = []
    for item in items:
        saved = ctx.stack._items.copy()
        joy_item = _ensure_joy_value(item)
        ctx.stack.push_value(joy_item)
        ctx.evaluator.execute(q)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if test_result.is_truthy():
            satisfies.append(joy_item)
        else:
            not_satisfies.append(joy_item)

    # Preserve original aggregate type for both partitions
    ctx.stack.push_value(_make_aggregate(tuple(satisfies), agg.type))
    ctx.stack.push_value(_make_aggregate(tuple(not_satisfies), agg.type))


@joy_word(name="fold", params=3, doc="A V [P] -> V'")
def fold(ctx: ExecutionContext) -> None:
    """Fold A with initial value V using binary operation P."""
    quot, init, agg = ctx.stack.pop_n(3)
    q = expect_quotation(quot, "fold")
    items = _get_aggregate(agg, "fold")

    acc = init
    for item in items:
        ctx.stack.push_value(acc)
        ctx.stack.push_value(_ensure_joy_value(item))
        ctx.evaluator.execute(q)
        acc = ctx.stack.pop()

    ctx.stack.push_value(acc)


@joy_word(name="each", params=2, doc="A [P] -> ...")
def each(ctx: ExecutionContext) -> None:
    """Execute P for each element of A (alias for step)."""
    quot, agg = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "each")
    items = _get_aggregate(agg, "each")

    for item in items:
        ctx.stack.push_value(_ensure_joy_value(item))
        ctx.evaluator.execute(q)


@joy_word(name="any", params=2, doc="A [P] -> B")
def any_combinator(ctx: ExecutionContext) -> None:
    """Test if P is true for any element of A."""
    quot, agg = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "any")
    items = _get_aggregate(agg, "any")

    for item in items:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(_ensure_joy_value(item))
        ctx.evaluator.execute(q)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if test_result.is_truthy():
            ctx.stack.push_value(JoyValue.boolean(True))
            return

    ctx.stack.push_value(JoyValue.boolean(False))


@joy_word(name="all", params=2, doc="A [P] -> B")
def all_combinator(ctx: ExecutionContext) -> None:
    """Test if P is true for all elements of A."""
    quot, agg = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "all")
    items = _get_aggregate(agg, "all")

    # Empty predicate returns false
    if len(q.terms) == 0:
        ctx.stack.push_value(JoyValue.boolean(False))
        return

    for item in items:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(_ensure_joy_value(item))
        ctx.evaluator.execute(q)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if not test_result.is_truthy():
            ctx.stack.push_value(JoyValue.boolean(False))
            return

    ctx.stack.push_value(JoyValue.boolean(True))


@joy_word(name="some", params=2, doc="A [P] -> B")
def some_combinator(ctx: ExecutionContext) -> None:
    """Test if P is true for some (at least one) element of A.

    With empty predicate, tests if any item is truthy.
    """
    quot, agg = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "some")
    items = _get_aggregate(agg, "some")

    for item in items:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(_ensure_joy_value(item))
        ctx.evaluator.execute(q)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if test_result.is_truthy():
            ctx.stack.push_value(JoyValue.boolean(True))
            return

    ctx.stack.push_value(JoyValue.boolean(False))


# -----------------------------------------------------------------------------
# Looping Combinators
# -----------------------------------------------------------------------------


@joy_word(name="times", params=2, doc="N [P] -> ...")
def times(ctx: ExecutionContext) -> None:
    """Execute P exactly N times."""
    quot, n = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "times")
    if n.type != JoyType.INTEGER:
        raise JoyTypeError("times", "INTEGER", n.type.name)

    count = n.value
    for _ in range(count):
        ctx.evaluator.execute(q)


@joy_word(name="while", params=2, doc="[B] [P] -> ...")
def while_loop(ctx: ExecutionContext) -> None:
    """While B is true, execute P."""
    p_quot, b_quot = ctx.stack.pop_n(2)
    b = expect_quotation(b_quot, "while")
    p = expect_quotation(p_quot, "while")

    while True:
        saved = ctx.stack._items.copy()
        ctx.evaluator.execute(b)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if not test_result.is_truthy():
            break

        ctx.evaluator.execute(p)


@joy_word(name="loop", params=1, doc="[P] -> ...")
def loop(ctx: ExecutionContext) -> None:
    """Execute P repeatedly until it leaves false on stack."""
    quot = ctx.stack.pop()
    q = expect_quotation(quot, "loop")

    while True:
        ctx.evaluator.execute(q)
        test_result = ctx.stack.pop()
        if not test_result.is_truthy():
            break


# -----------------------------------------------------------------------------
# Parallel Application Combinators
# -----------------------------------------------------------------------------


@joy_word(name="bi", params=3, doc="X [P] [Q] -> ...")
def bi(ctx: ExecutionContext) -> None:
    """Apply P to X, then apply Q to X."""
    q_quot, p_quot, x = ctx.stack.pop_n(3)
    p = expect_quotation(p_quot, "bi")
    q = expect_quotation(q_quot, "bi")

    ctx.stack.push_value(x)
    ctx.evaluator.execute(p)
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)


@joy_word(name="tri", params=4, doc="X [P] [Q] [R] -> ...")
def tri(ctx: ExecutionContext) -> None:
    """Apply P, Q, R to X in sequence."""
    r_quot, q_quot, p_quot, x = ctx.stack.pop_n(4)
    p = expect_quotation(p_quot, "tri")
    q = expect_quotation(q_quot, "tri")
    r = expect_quotation(r_quot, "tri")

    ctx.stack.push_value(x)
    ctx.evaluator.execute(p)
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)
    ctx.stack.push_value(x)
    ctx.evaluator.execute(r)


@joy_word(name="cleave", params=3, doc="X [P1] [P2] -> R1 R2")
def cleave(ctx: ExecutionContext) -> None:
    """Execute P1 and P2, each with X on top, producing two results."""
    p2_quot, p1_quot, x = ctx.stack.pop_n(3)
    p1 = expect_quotation(p1_quot, "cleave")
    p2 = expect_quotation(p2_quot, "cleave")

    # Execute P1 with X, save result
    ctx.stack.push_value(x)
    ctx.evaluator.execute(p1)
    r1 = ctx.stack.pop()

    # Execute P2 with X, get result
    ctx.stack.push_value(x)
    ctx.evaluator.execute(p2)
    r2 = ctx.stack.pop()

    # Push both results
    ctx.stack.push_value(r1)
    ctx.stack.push_value(r2)


@joy_word(name="spread", params=2, doc="X Y ... [P1 P2 ...] -> ...")
def spread(ctx: ExecutionContext) -> None:
    """Apply P1 to X, P2 to Y, etc."""
    quots = ctx.stack.pop()
    quot_list = _get_aggregate(quots, "spread")

    if not quot_list:
        return

    values = list(ctx.stack.pop_n(len(quot_list)))
    values.reverse()

    for val, q_val in zip(values, quot_list):
        if isinstance(q_val, JoyValue) and q_val.type == JoyType.QUOTATION:
            ctx.stack.push_value(val)
            ctx.evaluator.execute(q_val.value)
        elif isinstance(q_val, JoyQuotation):
            ctx.stack.push_value(val)
            ctx.evaluator.execute(q_val)


@joy_word(name="infra", params=2, doc="L [P] -> L'")
def infra(ctx: ExecutionContext) -> None:
    """Execute P with L as the stack, return new stack as list."""
    quot, lst = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "infra")
    items = _get_aggregate(lst, "infra")

    saved = ctx.stack._items.copy()
    # Input list is TOS-first, stack is bottom-first, so reverse
    ctx.stack._items = [_ensure_joy_value(item) for item in reversed(items)]
    ctx.evaluator.execute(q)
    # Result should be TOS-first, stack is bottom-first, so reverse
    result = tuple(reversed(ctx.stack._items))
    ctx.stack._items = saved
    ctx.stack.push_value(JoyValue.list(result))


@joy_word(name="app1", params=2, doc="X [P] -> X'")
def app1(ctx: ExecutionContext) -> None:
    """Apply P to X, leaving result."""
    quot, x = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "app1")
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)


@joy_word(name="app11", params=3, doc="X Y [P] -> Z")
def app11(ctx: ExecutionContext) -> None:
    """Apply P to X and Y."""
    quot, y, x = ctx.stack.pop_n(3)
    q = expect_quotation(quot, "app11")
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)
    ctx.evaluator.execute(q)


@joy_word(name="app12", params=3, doc="X Y1 Y2 [P] -> Z1 Z2")
def app12(ctx: ExecutionContext) -> None:
    """Apply P to (X,Y1) and (X,Y2)."""
    quot, y2, y1, x = ctx.stack.pop_n(4)
    q = expect_quotation(quot, "app12")

    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x)
    ctx.stack.push_value(y1)
    ctx.evaluator.execute(q)
    r1 = ctx.stack.pop()
    ctx.stack._items = saved

    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x)
    ctx.stack.push_value(y2)
    ctx.evaluator.execute(q)
    r2 = ctx.stack.pop()
    ctx.stack._items = saved

    ctx.stack.push_value(r1)
    ctx.stack.push_value(r2)


@joy_word(name="app2", params=3, doc="X Y [P] -> X' Y'")
def app2(ctx: ExecutionContext) -> None:
    """Apply P to X and Y separately, leaving both results."""
    quot, y, x = ctx.stack.pop_n(3)
    q = expect_quotation(quot, "app2")

    saved = ctx.stack._items.copy()
    ctx.stack.push_value(x)
    ctx.evaluator.execute(q)
    x_result = ctx.stack.pop()
    ctx.stack._items = saved

    saved = ctx.stack._items.copy()
    ctx.stack.push_value(y)
    ctx.evaluator.execute(q)
    y_result = ctx.stack.pop()
    ctx.stack._items = saved

    ctx.stack.push_value(x_result)
    ctx.stack.push_value(y_result)


@joy_word(name="app3", params=4, doc="X Y Z [P] -> X' Y' Z'")
def app3(ctx: ExecutionContext) -> None:
    """Apply P to X, Y, Z separately, leaving all results."""
    quot, z, y, x = ctx.stack.pop_n(4)
    q = expect_quotation(quot, "app3")

    results = []
    for val in [x, y, z]:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(val)
        ctx.evaluator.execute(q)
        results.append(ctx.stack.pop())
        ctx.stack._items = saved

    for r in results:
        ctx.stack.push_value(r)


@joy_word(name="app4", params=5, doc="W X Y Z [P] -> W' X' Y' Z'")
def app4(ctx: ExecutionContext) -> None:
    """Apply P to W, X, Y, Z separately."""
    quot, z, y, x, w = ctx.stack.pop_n(5)
    q = expect_quotation(quot, "app4")

    results = []
    for val in [w, x, y, z]:
        saved = ctx.stack._items.copy()
        ctx.stack.push_value(val)
        ctx.evaluator.execute(q)
        results.append(ctx.stack.pop())
        ctx.stack._items = saved

    for r in results:
        ctx.stack.push_value(r)


@joy_word(name="construct", params=2, doc="[P] [[Q1] [Q2] ...] -> R1 R2 ...")
def construct(ctx: ExecutionContext) -> None:
    """Save stack, execute P, then apply each Qi pushing results to saved stack."""
    quots, p_quot = ctx.stack.pop_n(2)
    p = expect_quotation(p_quot, "construct")
    quot_list = _get_aggregate(quots, "construct")

    # Save original stack state
    original_stack = ctx.stack._items.copy()

    # Execute P to prepare the working stack
    ctx.evaluator.execute(p)

    # Save the state after P for repeated use
    after_p = ctx.stack._items.copy()

    # Apply each quotation, pushing results onto original stack
    for q_val in quot_list:
        ctx.stack._items = after_p.copy()
        if isinstance(q_val, JoyValue) and q_val.type == JoyType.QUOTATION:
            ctx.evaluator.execute(q_val.value)
        elif isinstance(q_val, JoyQuotation):
            ctx.evaluator.execute(q_val)
        original_stack.append(ctx.stack.pop())

    # Restore to original stack with results appended
    ctx.stack._items = original_stack


@joy_word(name="compose", params=2, doc="[P] [Q] -> [[P] [Q] concat]")
def compose(ctx: ExecutionContext) -> None:
    """Compose two quotations into one."""
    q2, q1 = ctx.stack.pop_n(2)
    p1 = expect_quotation(q1, "compose")
    p2 = expect_quotation(q2, "compose")

    combined = JoyQuotation(p1.terms + p2.terms)
    ctx.stack.push_value(JoyValue.quotation(combined))


# -----------------------------------------------------------------------------
# Recursion Combinators
# -----------------------------------------------------------------------------


@joy_word(name="primrec", params=3, doc="X [I] [C] -> R")
def primrec(ctx: ExecutionContext) -> None:
    """Primitive recursion.

    Pushes all members of X onto stack, executes I for initial value,
    then executes C repeatedly to combine.
    """
    c_quot, i_quot, x = ctx.stack.pop_n(3)
    i = expect_quotation(i_quot, "primrec")
    c = expect_quotation(c_quot, "primrec")

    # First, push all members onto stack
    n = 0
    if x.type == JoyType.INTEGER:
        # For integer: push n, n-1, ..., 2, 1 (so 1 ends up on top)
        for j in range(x.value, 0, -1):
            ctx.stack.push(j)
            n += 1
    elif x.type in (JoyType.LIST, JoyType.QUOTATION):
        items = x.value if x.type == JoyType.LIST else x.value.terms
        for item in items:
            if isinstance(item, JoyValue):
                ctx.stack.push_value(item)
            else:
                ctx.stack.push(item)
            n += 1
    elif x.type == JoyType.STRING:
        for ch in x.value:
            ctx.stack.push(ch)
            n += 1
    elif x.type == JoyType.SET:
        for member in sorted(x.value):
            ctx.stack.push(member)
            n += 1
    else:
        raise JoyTypeError("primrec", "integer or aggregate", x.type.name)

    # Execute I for initial value
    ctx.evaluator.execute(i)

    # Execute C n times to combine
    for _ in range(n):
        ctx.evaluator.execute(c)


@joy_word(name="linrec", params=4, doc="[P] [T] [R1] [R2] -> ...")
def linrec(ctx: ExecutionContext) -> None:
    """Linear recursion combinator.

    Iterative implementation to avoid Python stack overflow with deep recursion.
    Equivalent to: [P] [T] [R1] [R2] linrec
    If P then T else R1 [P] [T] [R1] [R2] linrec R2
    """
    r2_quot, r1_quot, t_quot, p_quot = ctx.stack.pop_n(4)
    p = expect_quotation(p_quot, "linrec")
    t = expect_quotation(t_quot, "linrec")
    r1 = expect_quotation(r1_quot, "linrec")
    r2 = expect_quotation(r2_quot, "linrec")

    # Count how many times we need to execute R2 after the base case
    depth = 0

    while True:
        # Test P (non-destructively)
        saved = ctx.stack._items.copy()
        ctx.evaluator.execute(p)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if test_result.is_truthy():
            # Base case: execute T and exit loop
            ctx.evaluator.execute(t)
            break
        else:
            # Recursive case: execute R1 and continue
            ctx.evaluator.execute(r1)
            depth += 1

    # Execute R2 'depth' times (unwinding the recursion)
    for _ in range(depth):
        ctx.evaluator.execute(r2)


@joy_word(name="binrec", params=4, doc="[P] [T] [R1] [R2] -> ...")
def binrec(ctx: ExecutionContext) -> None:
    """Binary recursion combinator (divide and conquer)."""
    r2_quot, r1_quot, t_quot, p_quot = ctx.stack.pop_n(4)
    p = expect_quotation(p_quot, "binrec")
    t = expect_quotation(t_quot, "binrec")
    r1 = expect_quotation(r1_quot, "binrec")
    r2 = expect_quotation(r2_quot, "binrec")

    def binrec_aux() -> None:
        saved = ctx.stack._items.copy()
        ctx.evaluator.execute(p)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if test_result.is_truthy():
            ctx.evaluator.execute(t)
        else:
            ctx.evaluator.execute(r1)
            first_arg = ctx.stack.pop()
            binrec_aux()
            first_result = ctx.stack.pop()
            ctx.stack.push_value(first_arg)
            binrec_aux()
            ctx.stack.push_value(first_result)
            ctx.evaluator.execute(r2)

    binrec_aux()


@joy_word(name="tailrec", params=3, doc="[P] [T] [R1] -> ...")
def tailrec(ctx: ExecutionContext) -> None:
    """Tail recursion combinator."""
    r1_quot, t_quot, p_quot = ctx.stack.pop_n(3)
    p = expect_quotation(p_quot, "tailrec")
    t = expect_quotation(t_quot, "tailrec")
    r1 = expect_quotation(r1_quot, "tailrec")

    while True:
        saved = ctx.stack._items.copy()
        ctx.evaluator.execute(p)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if test_result.is_truthy():
            ctx.evaluator.execute(t)
            break
        else:
            ctx.evaluator.execute(r1)


@joy_word(name="genrec", params=4, doc="[B] [T] [R1] [R2] -> ...")
def genrec(ctx: ExecutionContext) -> None:
    """General recursion combinator."""
    r2_quot, r1_quot, t_quot, b_quot = ctx.stack.pop_n(4)
    b = expect_quotation(b_quot, "genrec")
    t = expect_quotation(t_quot, "genrec")
    r1 = expect_quotation(r1_quot, "genrec")
    r2 = expect_quotation(r2_quot, "genrec")

    def genrec_aux() -> None:
        saved = ctx.stack._items.copy()
        ctx.evaluator.execute(b)
        test_result = ctx.stack.pop()
        ctx.stack._items = saved

        if test_result.is_truthy():
            ctx.evaluator.execute(t)
        else:
            ctx.evaluator.execute(r1)
            rec_quot = JoyQuotation(
                (
                    JoyValue.quotation(b),
                    JoyValue.quotation(t),
                    JoyValue.quotation(r1),
                    JoyValue.quotation(r2),
                    "genrec",
                )
            )
            ctx.stack.push_value(JoyValue.quotation(rec_quot))
            ctx.evaluator.execute(r2)

    genrec_aux()


@joy_word(name="condlinrec", params=1, doc="[[C1] [C2] ... [D]] -> ...")
def condlinrec(ctx: ExecutionContext) -> None:
    """Conditional linear recursion.

    Each [Ci] is [[B] [T]] or [[B] [R1] [R2]].
    Tests each B. If true and just [T], executes T and exits.
    If true and [R1] [R2], executes R1, recurses, executes R2.
    Last clause [D] is default: [[T]] or [[R1] [R2]] (no condition).
    """
    clauses = ctx.stack.pop()
    clause_list = _get_aggregate(clauses, "condlinrec")

    if not clause_list:
        return

    def condlinrec_aux() -> None:
        saved = ctx.stack._items.copy()

        # Test all clauses except last (which is default)
        matched = False
        matched_idx = len(clause_list) - 1  # Default to last

        for i in range(len(clause_list) - 1):
            clause = clause_list[i]
            if not isinstance(clause, JoyValue) or clause.type != JoyType.QUOTATION:
                continue
            clause_terms = clause.value.terms
            if len(clause_terms) < 2:
                continue

            # Test condition B (first element)
            ctx.stack._items = saved.copy()
            condition = clause_terms[0]
            if isinstance(condition, JoyValue) and condition.type == JoyType.QUOTATION:
                ctx.evaluator.execute(condition.value)
            elif isinstance(condition, JoyQuotation):
                ctx.evaluator.execute(condition)
            else:
                ctx.evaluator._execute_term(condition)

            test_result = ctx.stack.pop()
            if test_result.is_truthy():
                matched = True
                matched_idx = i
                break

        # Restore stack
        ctx.stack._items = saved

        # Get clause to execute
        clause = clause_list[matched_idx]
        if not isinstance(clause, JoyValue) or clause.type != JoyType.QUOTATION:
            return
        clause_terms = clause.value.terms

        # Determine parts to execute:
        # If matched: skip B (element 0), use elements 1+ as [T] or [R1 R2...]
        # If default: use all elements as [T] or [R1 R2...]
        start_idx = 1 if matched else 0
        parts = clause_terms[start_idx:]

        if not parts:
            return

        # Execute first part
        first_part = parts[0]
        if isinstance(first_part, JoyValue) and first_part.type == JoyType.QUOTATION:
            ctx.evaluator.execute(first_part.value)
        elif isinstance(first_part, JoyQuotation):
            ctx.evaluator.execute(first_part)
        else:
            ctx.evaluator._execute_term(first_part)

        # For each subsequent part: recurse, then execute
        for j in range(1, len(parts)):
            condlinrec_aux()
            part = parts[j]
            if isinstance(part, JoyValue) and part.type == JoyType.QUOTATION:
                ctx.evaluator.execute(part.value)
            elif isinstance(part, JoyQuotation):
                ctx.evaluator.execute(part)
            else:
                ctx.evaluator._execute_term(part)

    condlinrec_aux()


@joy_word(name="condnestrec", params=1, doc="[[B1 R1] [B2 R2] ... [D]] -> ...")
def condnestrec(ctx: ExecutionContext) -> None:
    """Conditional nested recursion."""
    clauses = ctx.stack.pop()
    clause_list = _get_aggregate(clauses, "condnestrec")

    def condnestrec_aux() -> None:
        saved = ctx.stack._items.copy()

        for clause in clause_list:
            if not isinstance(clause, JoyValue) or clause.type != JoyType.QUOTATION:
                continue

            clause_terms = clause.value.terms
            if len(clause_terms) < 1:
                continue

            if len(clause_terms) == 1:
                ctx.stack._items = saved.copy()
                term = clause_terms[0]
                if isinstance(term, JoyValue) and term.type == JoyType.QUOTATION:
                    ctx.evaluator.execute(term.value)
                elif isinstance(term, JoyQuotation):
                    ctx.evaluator.execute(term)
                elif isinstance(term, str):
                    if term == "condnestrec":
                        condnestrec_aux()
                    else:
                        ctx.evaluator._execute_symbol(term)
                return

            condition = clause_terms[0]
            body = clause_terms[1]

            ctx.stack._items = saved.copy()
            if isinstance(condition, JoyValue) and condition.type == JoyType.QUOTATION:
                ctx.evaluator.execute(condition.value)
            elif isinstance(condition, JoyQuotation):
                ctx.evaluator.execute(condition)
            elif isinstance(condition, str):
                ctx.evaluator._execute_symbol(condition)
            else:
                ctx.stack.push_value(condition)

            test_result = ctx.stack.pop()

            if test_result.is_truthy():
                ctx.stack._items = saved.copy()
                _execute_body_with_recursion(body, condnestrec_aux)
                return

        ctx.stack._items = saved

    def _execute_body_with_recursion(body, recurse_fn):
        if isinstance(body, JoyValue) and body.type == JoyType.QUOTATION:
            _execute_terms_with_recursion(body.value.terms, recurse_fn)
        elif isinstance(body, JoyQuotation):
            _execute_terms_with_recursion(body.terms, recurse_fn)
        elif isinstance(body, str):
            if body == "condnestrec":
                recurse_fn()
            else:
                ctx.evaluator._execute_symbol(body)

    def _execute_terms_with_recursion(terms, recurse_fn):
        for term in terms:
            if isinstance(term, str) and term == "condnestrec":
                recurse_fn()
            elif isinstance(term, JoyValue):
                ctx.evaluator._execute_term(term)
            elif isinstance(term, JoyQuotation):
                ctx.stack.push_value(JoyValue.quotation(term))
            else:
                ctx.evaluator._execute_term(term)

    condnestrec_aux()


# -----------------------------------------------------------------------------
# Tree Combinators
# -----------------------------------------------------------------------------


@joy_word(name="treestep", params=2, doc="T [P] -> ...")
def treestep(ctx: ExecutionContext) -> None:
    """Tree step: apply P to each node."""
    quot, tree = ctx.stack.pop_n(2)
    q = expect_quotation(quot, "treestep")

    def step_tree(node: JoyValue) -> None:
        if node.type in (JoyType.LIST, JoyType.QUOTATION):
            items = node.value if node.type == JoyType.LIST else node.value.terms
            for item in items:
                if isinstance(item, JoyValue):
                    step_tree(item)
        else:
            ctx.stack.push_value(node)
            ctx.evaluator.execute(q)

    step_tree(tree)


@joy_word(name="treerec", params=3, doc="T [O] [C] -> ...")
def treerec(ctx: ExecutionContext) -> None:
    """Tree recursion: If T is leaf, execute O. Else execute [[O] [C] treerec] C."""
    c_quot, o_quot, tree = ctx.stack.pop_n(3)
    o = expect_quotation(o_quot, "treerec")
    c = expect_quotation(c_quot, "treerec")

    def treerec_aux(node: JoyValue) -> None:
        if node.type in (JoyType.LIST, JoyType.QUOTATION):
            # Non-leaf: push node, push [[O] [C] treerec], execute C
            ctx.stack.push_value(node)
            # Build the recursive quotation [[O] [C] treerec]
            rec_quot = JoyQuotation(
                (
                    JoyValue.quotation(o),
                    JoyValue.quotation(c),
                    "treerec",
                )
            )
            ctx.stack.push_value(JoyValue.quotation(rec_quot))
            ctx.evaluator.execute(c)
        else:
            # Leaf: push node, execute O
            ctx.stack.push_value(node)
            ctx.evaluator.execute(o)

    treerec_aux(tree)


@joy_word(name="treegenrec", params=4, doc="T [O1] [O2] [C] -> ...")
def treegenrec(ctx: ExecutionContext) -> None:
    """General tree recursion.

    If T is leaf, execute O1. Else execute O2 then [[O1] [O2] [C] treegenrec] C.
    """
    c_quot, o2_quot, o1_quot, tree = ctx.stack.pop_n(4)
    o1 = expect_quotation(o1_quot, "treegenrec")
    o2 = expect_quotation(o2_quot, "treegenrec")
    c = expect_quotation(c_quot, "treegenrec")

    if tree.type in (JoyType.LIST, JoyType.QUOTATION):
        # Non-leaf: push tree, execute O2, push [[O1] [O2] [C] treegenrec], execute C
        ctx.stack.push_value(tree)
        ctx.evaluator.execute(o2)
        # Build the recursive quotation [[O1] [O2] [C] treegenrec]
        rec_quot = JoyQuotation(
            (
                JoyValue.quotation(o1),
                JoyValue.quotation(o2),
                JoyValue.quotation(c),
                "treegenrec",
            )
        )
        ctx.stack.push_value(JoyValue.quotation(rec_quot))
        ctx.evaluator.execute(c)
    else:
        # Leaf: push tree, execute O1
        ctx.stack.push_value(tree)
        ctx.evaluator.execute(o1)
