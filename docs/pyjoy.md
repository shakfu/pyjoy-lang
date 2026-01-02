# pyjoy.md

Analysis and design document for reimplementing Joy in Python 3 with Python function extensibility.

## 1. Overview

### 1.1 Goals

1. **Faithful Joy Semantics**: Preserve the concatenative, stack-based execution model
2. **Python Extensibility**: Allow defining new Joy words as Python functions
3. **Interoperability**: Enable Joy programs to call Python and vice versa
4. **Simplicity**: Leverage Python's features for cleaner implementation
5. **Performance**: Acceptable performance for interactive use (not C-speed)
6. **C code emitter**: Generate c code which can then be compiled into machine code

### 1.2 Non-Goals

- Exact C API compatibility
- Bytecode compilation to Python
- Multi-threading (Joy is inherently single-threaded)

---

## 2. Architecture Design

### 2.1 Core Components

```text
+------------------+     +------------------+     +------------------+
|     Scanner      | --> |      Parser      | --> |    Evaluator     |
| (Tokenization)   |     | (AST Building)   |     | (Stack Machine)  |
+------------------+     +------------------+     +------------------+
        |                        |                        |
        v                        v                        v
+------------------+     +------------------+     +------------------+
|   Token Stream   |     |   Joy AST        |     |   Joy Stack      |
|   (generator)    |     |   (nested lists) |     |   (Python list)  |
+------------------+     +------------------+     +------------------+
                                                          |
                                                          v
                                                 +------------------+
                                                 |  Symbol Table    |
                                                 |  (dict)          |
                                                 +------------------+
```

### 2.2 Module Structure

```
pyjoy/
    __init__.py          # Public API
    scanner.py           # Lexical analysis
    parser.py            # AST construction
    evaluator.py         # Stack machine execution
    types.py             # Joy type wrappers
    stack.py             # Stack implementation
    builtins/
        __init__.py      # Builtin registration
        stack_ops.py     # dup, swap, pop, etc.
        arithmetic.py    # +, -, *, /, etc.
        list_ops.py      # cons, first, rest, map, filter
        control.py       # ifte, while, linrec, binrec
        io.py            # put, get, file operations
    stdlib/
        *.joy            # Joy library files
```

### 2.3 Execution Flow

```python
# High-level execution
source = "[1 2 3] [dup *] map"
tokens = scanner.tokenize(source)      # Iterator of tokens
ast = parser.parse(tokens)             # Nested list structure
evaluator.execute(ast)                 # Stack manipulation
result = evaluator.stack.peek()        # [1 4 9]
```

---

## 3. Type System

### 3.1 Joy to Python Type Mapping

| Joy Type      | Python Type   | Notes                                             |
|---------------|---------------|---------------------------------------------------|
| `INTEGER`     | `int`         | Python int is arbitrary precision; Joy is 64-bit  |
| `FLOAT`       | `float`       | IEEE 754 double precision                         |
| `STRING`      | `str`         | UTF-8 strings                                     |
| `CHAR`        | `str` (len 1) | Single character string                           |
| `BOOLEAN`     | `bool`        | True/False                                        |
| `LIST`        | `tuple`       | Immutable for Joy semantics                       |
| `SET`         | `frozenset`   | Immutable; members restricted to 0-63             |
| `FILE`        | `IO`          | Python file object                                |
| `QUOTATION`   | `JoyQuotation`| Wrapper for unevaluated code                      |
| `SYMBOL`      | `str`         | Symbol name for user definitions                  |

### 3.2 Type Wrapper Classes

```python
from dataclasses import dataclass
from typing import Any, Tuple, FrozenSet, IO, Callable
from enum import Enum, auto

class JoyType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    CHAR = auto()
    BOOLEAN = auto()
    LIST = auto()
    SET = auto()
    FILE = auto()
    QUOTATION = auto()
    SYMBOL = auto()


@dataclass(frozen=True)
class JoyValue:
    """Tagged union for Joy values"""
    type: JoyType
    value: Any

    @classmethod
    def integer(cls, n: int) -> 'JoyValue':
        return cls(JoyType.INTEGER, n)

    @classmethod
    def floating(cls, f: float) -> 'JoyValue':
        return cls(JoyType.FLOAT, f)

    @classmethod
    def string(cls, s: str) -> 'JoyValue':
        return cls(JoyType.STRING, s)

    @classmethod
    def char(cls, c: str) -> 'JoyValue':
        assert len(c) == 1
        return cls(JoyType.CHAR, c)

    @classmethod
    def boolean(cls, b: bool) -> 'JoyValue':
        return cls(JoyType.BOOLEAN, b)

    @classmethod
    def list(cls, items: Tuple) -> 'JoyValue':
        return cls(JoyType.LIST, items)

    @classmethod
    def joy_set(cls, members: FrozenSet[int]) -> 'JoyValue':
        # Validate members are in range [0, 63]
        for m in members:
            if not (0 <= m <= 63):
                raise ValueError(f"Set member {m} out of range [0, 63]")
        return cls(JoyType.SET, members)

    @classmethod
    def quotation(cls, code: 'JoyQuotation') -> 'JoyValue':
        return cls(JoyType.QUOTATION, code)


class JoyQuotation:
    """Represents unevaluated Joy code [...] """

    def __init__(self, terms: Tuple[Any, ...]):
        self.terms = terms

    def __repr__(self):
        return f"[{' '.join(str(t) for t in self.terms)}]"

    def __iter__(self):
        return iter(self.terms)
```

### 3.3 Automatic Type Inference

```python
def python_to_joy(value: Any) -> JoyValue:
    """Convert Python value to Joy value with type inference"""
    if isinstance(value, JoyValue):
        return value
    elif isinstance(value, bool):
        return JoyValue.boolean(value)
    elif isinstance(value, int):
        return JoyValue.integer(value)
    elif isinstance(value, float):
        return JoyValue.floating(value)
    elif isinstance(value, str):
        if len(value) == 1:
            return JoyValue.char(value)
        return JoyValue.string(value)
    elif isinstance(value, (list, tuple)):
        return JoyValue.list(tuple(python_to_joy(x) for x in value))
    elif isinstance(value, frozenset):
        return JoyValue.joy_set(value)
    elif isinstance(value, JoyQuotation):
        return JoyValue.quotation(value)
    else:
        raise TypeError(f"Cannot convert {type(value)} to Joy")


def joy_to_python(value: JoyValue) -> Any:
    """Convert Joy value to native Python value"""
    if value.type == JoyType.LIST:
        return tuple(joy_to_python(JoyValue(t.type, t.value))
                     for t in value.value)
    elif value.type == JoyType.QUOTATION:
        return value.value  # Keep as JoyQuotation
    else:
        return value.value
```

---

## 4. Stack Implementation

### 4.1 Core Stack Class

```python
from typing import List, Any, Optional

class JoyStack:
    """
    Joy evaluation stack.

    Uses Python list internally but provides Joy-like interface.
    Stack grows upward: index -1 is TOS (top of stack).
    """

    def __init__(self):
        self._items: List[JoyValue] = []

    def push(self, value: Any) -> None:
        """Push value onto stack, auto-converting to JoyValue"""
        self._items.append(python_to_joy(value))

    def pop(self) -> JoyValue:
        """Pop and return top of stack"""
        if not self._items:
            raise RuntimeError("Stack underflow")
        return self._items.pop()

    def peek(self, depth: int = 0) -> JoyValue:
        """
        Peek at stack item at given depth.
        depth=0 is TOS, depth=1 is second item, etc.
        """
        if depth >= len(self._items):
            raise IndexError(f"Stack depth {depth} exceeds size {len(self._items)}")
        return self._items[-(depth + 1)]

    def pop_n(self, n: int) -> Tuple[JoyValue, ...]:
        """Pop n items, return as tuple (TOS first)"""
        if n > len(self._items):
            raise RuntimeError(f"Cannot pop {n} items from stack of size {len(self._items)}")
        result = tuple(self._items[-n:])
        self._items = self._items[:-n]
        return result[::-1]  # Reverse so TOS is first

    def push_many(self, *values: Any) -> None:
        """Push multiple values (first arg pushed first)"""
        for v in values:
            self.push(v)

    @property
    def depth(self) -> int:
        """Current stack depth"""
        return len(self._items)

    def copy(self) -> 'JoyStack':
        """Create a shallow copy for state preservation"""
        new_stack = JoyStack()
        new_stack._items = self._items.copy()
        return new_stack

    def __repr__(self) -> str:
        return f"Stack({self._items})"
```

### 4.2 State Management (Dump Stack Equivalent)

```python
class ExecutionContext:
    """
    Manages execution state including saved stacks.
    Equivalent to C's env->dump, env->dump1, etc.
    """

    def __init__(self):
        self.stack = JoyStack()
        self._saved_states: List[List[JoyValue]] = []

    def save_stack(self) -> int:
        """
        Save current stack state. Returns state ID.
        Equivalent to SAVESTACK macro.
        """
        self._saved_states.append(self.stack._items.copy())
        return len(self._saved_states) - 1

    def restore_stack(self, state_id: int) -> None:
        """Restore stack to saved state"""
        self.stack._items = self._saved_states[state_id].copy()

    def pop_saved(self) -> None:
        """Pop most recent saved state. Equivalent to POP(env->dump)"""
        if self._saved_states:
            self._saved_states.pop()

    def get_saved(self, state_id: int, depth: int) -> JoyValue:
        """
        Get item from saved state.
        Equivalent to SAVED1, SAVED2, etc.
        """
        saved = self._saved_states[state_id]
        return saved[-(depth + 1)]
```

---

## 5. Python Extensibility API

### 5.1 Decorator-Based Primitive Definition

```python
from functools import wraps
from typing import Callable, Optional, Dict, List

# Registry for primitives
_primitives: Dict[str, Callable] = {}


def joy_word(name: str = None,
             params: int = 0,
             types: Dict[int, JoyType] = None,
             doc: str = None):
    """
    Decorator to define a Joy word implemented in Python.

    Args:
        name: Joy word name (defaults to function name)
        params: Required stack parameters
        types: Type requirements {depth: JoyType}
        doc: Documentation string (Joy signature)

    Example:
        @joy_word(name="+", params=2, doc="N1 N2 -> N3")
        def plus(ctx):
            b, a = ctx.stack.pop_n(2)
            ctx.stack.push(a.value + b.value)
    """
    def decorator(func: Callable) -> Callable:
        word_name = name or func.__name__

        @wraps(func)
        def wrapper(ctx: ExecutionContext) -> None:
            # Validate parameter count
            if ctx.stack.depth < params:
                raise RuntimeError(
                    f"{word_name}: requires {params} parameters, "
                    f"stack has {ctx.stack.depth}")

            # Validate types
            if types:
                for depth, expected_type in types.items():
                    actual = ctx.stack.peek(depth)
                    if actual.type != expected_type:
                        raise TypeError(
                            f"{word_name}: parameter {depth} expected "
                            f"{expected_type.name}, got {actual.type.name}")

            # Execute primitive
            return func(ctx)

        wrapper.joy_word = word_name
        wrapper.joy_params = params
        wrapper.joy_doc = doc or func.__doc__

        _primitives[word_name] = wrapper
        return wrapper

    return decorator


def register_primitive(name: str, func: Callable) -> None:
    """Register a primitive without decorator"""
    _primitives[name] = func


def get_primitive(name: str) -> Optional[Callable]:
    """Get registered primitive by name"""
    return _primitives.get(name)
```

### 5.2 Example Primitive Implementations

```python
# Stack operations
@joy_word(name="dup", params=1, doc="X -> X X")
def dup(ctx: ExecutionContext) -> None:
    """Duplicate top of stack"""
    ctx.stack.push(ctx.stack.peek())


@joy_word(name="pop", params=1, doc="X ->")
def pop(ctx: ExecutionContext) -> None:
    """Remove top of stack"""
    ctx.stack.pop()


@joy_word(name="swap", params=2, doc="X Y -> Y X")
def swap(ctx: ExecutionContext) -> None:
    """Exchange top two stack items"""
    b, a = ctx.stack.pop_n(2)
    ctx.stack.push_many(b, a)


# Arithmetic
@joy_word(name="+", params=2, doc="N1 N2 -> N3")
def plus(ctx: ExecutionContext) -> None:
    """Add two numbers"""
    b, a = ctx.stack.pop_n(2)
    # Type coercion: if either is float, result is float
    if a.type == JoyType.FLOAT or b.type == JoyType.FLOAT:
        result = float(a.value) + float(b.value)
    else:
        result = a.value + b.value
    ctx.stack.push(result)


@joy_word(name="*", params=2, doc="N1 N2 -> N3")
def mul(ctx: ExecutionContext) -> None:
    """Multiply two numbers"""
    b, a = ctx.stack.pop_n(2)
    if a.type == JoyType.FLOAT or b.type == JoyType.FLOAT:
        result = float(a.value) * float(b.value)
    else:
        result = a.value * b.value
    ctx.stack.push(result)


# List operations
@joy_word(name="cons", params=2, doc="X L -> [X | L]")
def cons(ctx: ExecutionContext) -> None:
    """Prepend element to list"""
    lst, elem = ctx.stack.pop_n(2)
    if lst.type != JoyType.LIST:
        raise TypeError("cons: second argument must be list")
    result = (elem,) + lst.value
    ctx.stack.push(JoyValue.list(result))


@joy_word(name="first", params=1, types={0: JoyType.LIST}, doc="L -> X")
def first(ctx: ExecutionContext) -> None:
    """Get first element of list"""
    lst = ctx.stack.pop()
    if not lst.value:
        raise RuntimeError("first: empty list")
    ctx.stack.push(lst.value[0])


@joy_word(name="rest", params=1, types={0: JoyType.LIST}, doc="L -> L'")
def rest(ctx: ExecutionContext) -> None:
    """Get list without first element"""
    lst = ctx.stack.pop()
    if not lst.value:
        raise RuntimeError("rest: empty list")
    ctx.stack.push(JoyValue.list(lst.value[1:]))
```

### 5.3 Higher-Order Primitives (Quotation Execution)

```python
class Evaluator:
    """Joy evaluator with quotation execution support"""

    def __init__(self):
        self.ctx = ExecutionContext()
        self.definitions: Dict[str, JoyQuotation] = {}

    def execute(self, program: JoyQuotation) -> None:
        """Execute a quotation"""
        for term in program.terms:
            self._execute_term(term)

    def _execute_term(self, term: Any) -> None:
        """Execute a single term"""
        if isinstance(term, JoyValue):
            # Literal: push to stack
            self.ctx.stack.push(term)
        elif isinstance(term, JoyQuotation):
            # Quotation: push as value (don't execute)
            self.ctx.stack.push(JoyValue.quotation(term))
        elif isinstance(term, str):
            # Symbol: look up and execute
            if term in _primitives:
                _primitives[term](self.ctx)
            elif term in self.definitions:
                self.execute(self.definitions[term])
            else:
                raise NameError(f"Undefined word: {term}")
        else:
            # Unknown: try to convert and push
            self.ctx.stack.push(term)

    def execute_quotation_on_stack(self) -> None:
        """
        Execute quotation from top of stack.
        Used by 'i' and other combinators.
        """
        quot = self.ctx.stack.pop()
        if quot.type != JoyType.QUOTATION:
            raise TypeError("Expected quotation")
        self.execute(quot.value)


# Higher-order primitive: i (execute quotation)
@joy_word(name="i", params=1, types={0: JoyType.QUOTATION}, doc="[P] -> ...")
def i_combinator(ctx: ExecutionContext) -> None:
    """Execute quotation"""
    # Access evaluator through context (need to wire this up)
    quot = ctx.stack.pop()
    ctx._evaluator.execute(quot.value)


# Higher-order primitive: map
@joy_word(name="map", params=2, doc="A [P] -> B")
def map_combinator(ctx: ExecutionContext) -> None:
    """Apply quotation to each element of aggregate"""
    quot, aggregate = ctx.stack.pop_n(2)

    if quot.type != JoyType.QUOTATION:
        raise TypeError("map: second argument must be quotation")
    if aggregate.type != JoyType.LIST:
        raise TypeError("map: first argument must be list")

    results = []
    evaluator = ctx._evaluator

    for elem in aggregate.value:
        # Save stack state
        state_id = ctx.save_stack()

        # Push element and execute quotation
        ctx.stack.push(elem)
        evaluator.execute(quot.value)

        # Collect result
        result = ctx.stack.pop()
        results.append(result)

        # Restore stack
        ctx.restore_stack(state_id)

    ctx.pop_saved()
    ctx.stack.push(JoyValue.list(tuple(results)))


# Higher-order primitive: filter
@joy_word(name="filter", params=2, doc="A [B] -> A'")
def filter_combinator(ctx: ExecutionContext) -> None:
    """Keep elements where quotation returns true"""
    quot, aggregate = ctx.stack.pop_n(2)

    if quot.type != JoyType.QUOTATION:
        raise TypeError("filter: second argument must be quotation")
    if aggregate.type != JoyType.LIST:
        raise TypeError("filter: first argument must be list")

    results = []
    evaluator = ctx._evaluator

    for elem in aggregate.value:
        state_id = ctx.save_stack()

        ctx.stack.push(elem)
        evaluator.execute(quot.value)

        # Check boolean result
        result = ctx.stack.pop()
        if result.value:  # Truthy check
            results.append(elem)

        ctx.restore_stack(state_id)

    ctx.pop_saved()
    ctx.stack.push(JoyValue.list(tuple(results)))


# Higher-order primitive: ifte (if-then-else)
@joy_word(name="ifte", params=3, doc="[B] [T] [F] -> ...")
def ifte_combinator(ctx: ExecutionContext) -> None:
    """Conditional execution"""
    false_branch, true_branch, condition = ctx.stack.pop_n(3)

    for q in [condition, true_branch, false_branch]:
        if q.type != JoyType.QUOTATION:
            raise TypeError("ifte: all arguments must be quotations")

    evaluator = ctx._evaluator

    # Save stack for restoration
    state_id = ctx.save_stack()

    # Execute condition
    evaluator.execute(condition.value)
    test_result = ctx.stack.pop()

    # Restore stack
    ctx.restore_stack(state_id)

    # Execute appropriate branch
    if test_result.value:  # Truthy
        evaluator.execute(true_branch.value)
    else:
        evaluator.execute(false_branch.value)

    ctx.pop_saved()
```

### 5.4 Recursion Combinators

```python
@joy_word(name="linrec", params=4, doc="[P] [T] [R1] [R2] -> ...")
def linrec_combinator(ctx: ExecutionContext) -> None:
    """
    Linear recursion combinator.
    [P] = predicate, [T] = terminal, [R1] = reduce, [R2] = combine
    """
    r2, r1, terminal, predicate = ctx.stack.pop_n(4)
    evaluator = ctx._evaluator

    def linrec_aux():
        # Save stack state
        saved = ctx.stack._items.copy()

        # Execute predicate
        evaluator.execute(predicate.value)
        test_result = ctx.stack.pop()

        # Restore stack
        ctx.stack._items = saved

        if test_result.value:  # Base case
            evaluator.execute(terminal.value)
        else:  # Recursive case
            evaluator.execute(r1.value)  # Reduce
            linrec_aux()                  # Recurse
            evaluator.execute(r2.value)  # Combine

    linrec_aux()


@joy_word(name="binrec", params=4, doc="[P] [T] [R1] [R2] -> ...")
def binrec_combinator(ctx: ExecutionContext) -> None:
    """
    Binary recursion combinator (divide and conquer).
    [P] = predicate, [T] = terminal, [R1] = split, [R2] = combine
    """
    r2, r1, terminal, predicate = ctx.stack.pop_n(4)
    evaluator = ctx._evaluator

    def binrec_aux():
        saved = ctx.stack._items.copy()

        evaluator.execute(predicate.value)
        test_result = ctx.stack.pop()

        ctx.stack._items = saved

        if test_result.value:  # Base case
            evaluator.execute(terminal.value)
        else:  # Recursive case
            evaluator.execute(r1.value)  # Split into two

            # Save first result
            first_arg = ctx.stack.pop()

            # First recursion
            binrec_aux()
            first_result = ctx.stack.pop()

            # Restore and second recursion
            ctx.stack.push(first_arg)
            binrec_aux()

            # Push first result back
            ctx.stack.push(first_result)

            # Combine
            evaluator.execute(r2.value)

    binrec_aux()
```

---

## 6. Scanner and Parser

### 6.1 Scanner (Tokenizer)

```python
import re
from typing import Iterator, Tuple, Any
from dataclasses import dataclass

@dataclass
class Token:
    type: str
    value: Any
    line: int
    column: int


class Scanner:
    """Joy lexical analyzer"""

    # Token patterns
    PATTERNS = [
        ('COMMENT', r'\(\*.*?\*\)'),        # (* comment *)
        ('FLOAT', r'-?\d+\.\d+([eE][+-]?\d+)?'),
        ('INTEGER', r'-?\d+'),
        ('STRING', r'"([^"\\]|\\.)*"'),
        ('CHAR', r"'(.|\\.)'"),
        ('LBRACKET', r'\['),
        ('RBRACKET', r'\]'),
        ('LBRACE', r'\{'),
        ('RBRACE', r'\}'),
        ('SEMICOLON', r';'),
        ('PERIOD', r'\.'),
        ('DEFINE', r'=='),
        ('SYMBOL', r'[a-zA-Z_][a-zA-Z0-9_\-]*|[+\-*/<=>&|!?@#$%^~]+'),
        ('WHITESPACE', r'\s+'),
    ]

    def __init__(self):
        self.regex = re.compile(
            '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.PATTERNS)
        )

    def tokenize(self, source: str) -> Iterator[Token]:
        """Generate tokens from source code"""
        line = 1
        line_start = 0

        for match in self.regex.finditer(source):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - line_start

            # Track line numbers
            newlines = value.count('\n')
            if newlines:
                line += newlines
                line_start = match.end() - len(value.split('\n')[-1])

            # Skip whitespace and comments
            if kind in ('WHITESPACE', 'COMMENT'):
                continue

            # Convert token value
            if kind == 'INTEGER':
                value = int(value)
            elif kind == 'FLOAT':
                value = float(value)
            elif kind == 'STRING':
                value = self._unescape_string(value[1:-1])
            elif kind == 'CHAR':
                value = self._unescape_char(value[1:-1])

            yield Token(kind, value, line, column)

    def _unescape_string(self, s: str) -> str:
        """Process escape sequences in string"""
        return s.encode().decode('unicode_escape')

    def _unescape_char(self, c: str) -> str:
        """Process escape sequences in character literal"""
        if c.startswith('\\'):
            return self._unescape_string(c)
        return c
```

### 6.2 Parser

```python
from typing import List, Any, Optional

class Parser:
    """
    Joy parser: converts token stream to AST.

    AST is nested list structure:
    - Literals become JoyValue
    - Quotations become JoyQuotation
    - Symbols remain as strings
    """

    KEYWORDS = {'LIBRA', 'DEFINE', 'HIDE', 'IN', 'MODULE',
                'PRIVATE', 'PUBLIC', 'CONST', 'END'}

    def __init__(self):
        self.tokens: List[Token] = []
        self.pos: int = 0

    def parse(self, tokens: Iterator[Token]) -> JoyQuotation:
        """Parse token stream into program"""
        self.tokens = list(tokens)
        self.pos = 0

        terms = self._parse_terms()
        return JoyQuotation(tuple(terms))

    def _current(self) -> Optional[Token]:
        """Get current token"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self) -> Token:
        """Consume and return current token"""
        token = self._current()
        self.pos += 1
        return token

    def _parse_terms(self, terminators: set = None) -> List[Any]:
        """Parse sequence of terms until terminator"""
        terminators = terminators or {'PERIOD', 'SEMICOLON'}
        terms = []

        while True:
            token = self._current()
            if token is None or token.type in terminators:
                break

            term = self._parse_term()
            if term is not None:
                terms.append(term)

        return terms

    def _parse_term(self) -> Any:
        """Parse single term"""
        token = self._current()

        if token.type == 'INTEGER':
            self._advance()
            return JoyValue.integer(token.value)

        elif token.type == 'FLOAT':
            self._advance()
            return JoyValue.floating(token.value)

        elif token.type == 'STRING':
            self._advance()
            return JoyValue.string(token.value)

        elif token.type == 'CHAR':
            self._advance()
            return JoyValue.char(token.value)

        elif token.type == 'LBRACKET':
            return self._parse_quotation()

        elif token.type == 'LBRACE':
            return self._parse_set()

        elif token.type == 'SYMBOL':
            self._advance()
            value = token.value
            # Handle boolean literals
            if value == 'true':
                return JoyValue.boolean(True)
            elif value == 'false':
                return JoyValue.boolean(False)
            # Otherwise return as symbol
            return value

        elif token.type == 'DEFINE':
            # Definition: handled at statement level
            self._advance()
            return None

        else:
            raise SyntaxError(f"Unexpected token: {token}")

    def _parse_quotation(self) -> JoyQuotation:
        """Parse [...] quotation"""
        self._advance()  # Consume '['
        terms = self._parse_terms({'RBRACKET'})

        if self._current() is None or self._current().type != 'RBRACKET':
            raise SyntaxError("Expected ']'")
        self._advance()  # Consume ']'

        return JoyQuotation(tuple(terms))

    def _parse_set(self) -> JoyValue:
        """Parse {...} set literal"""
        self._advance()  # Consume '{'
        terms = self._parse_terms({'RBRACE'})

        if self._current() is None or self._current().type != 'RBRACE':
            raise SyntaxError("Expected '}'")
        self._advance()  # Consume '}'

        # Convert to set
        members = set()
        for term in terms:
            if isinstance(term, JoyValue) and term.type == JoyType.INTEGER:
                members.add(term.value)
            else:
                raise SyntaxError("Set members must be integers")

        return JoyValue.joy_set(frozenset(members))
```

---

## 7. Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Type system (`types.py`)
- [ ] Stack implementation (`stack.py`)
- [ ] Scanner (`scanner.py`)
- [ ] Basic parser (`parser.py`)
- [ ] Evaluator skeleton (`evaluator.py`)

### Phase 2: Basic Primitives (Week 2)
- [ ] Stack operations: `dup`, `swap`, `pop`, `over`, `rotate`
- [ ] Arithmetic: `+`, `-`, `*`, `/`, `rem`
- [ ] Comparison: `<`, `>`, `<=`, `>=`, `=`, `!=`
- [ ] Boolean: `and`, `or`, `not`
- [ ] List basics: `cons`, `first`, `rest`, `null`, `size`

### Phase 3: Higher-Order Operations (Week 3)
- [ ] Execution: `i`, `x`, `dip`
- [ ] Conditionals: `ifte`, `branch`, `choice`
- [ ] Iteration: `map`, `filter`, `fold`, `step`
- [ ] Looping: `while`, `times`

### Phase 4: Recursion Combinators (Week 4)
- [ ] `linrec` (linear recursion)
- [ ] `binrec` (binary recursion)
- [ ] `genrec` (general recursion)
- [ ] `primrec` (primitive recursion)
- [ ] `tailrec` (tail recursion)

### Phase 5: I/O and System (Week 5)
- [ ] Output: `put`, `putch`, `putchars`
- [ ] Input: `get`, `getch`
- [ ] Files: `fopen`, `fclose`, `fread`, `fwrite`
- [ ] System: `include`, `quit`, `abort`

### Phase 6: Module System (Week 6)
- [ ] Definitions: `DEFINE`, `==`
- [ ] Modules: `MODULE`, `END`
- [ ] Visibility: `HIDE`, `PRIVATE`, `PUBLIC`
- [ ] Constants: `CONST`

### Phase 7: Standard Library (Week 7-8)
- [ ] Port Joy library files from `lib/`
- [ ] Test compatibility with C implementation
- [ ] Documentation

---

## 8. Design Decisions

### 8.1 Why Tuples for Lists?

Joy lists are immutable (functional semantics). Python tuples:
- Are immutable (matches Joy semantics)
- Have O(1) indexing (unlike linked lists)
- Are hashable (can be used in sets/dicts)

**Trade-off:** `cons` is O(n) in Python tuples vs O(1) in linked lists.

**Alternative:** Use a custom linked list class if `cons` performance is critical:

```python
@dataclass(frozen=True)
class Cons:
    head: Any
    tail: Optional['Cons']

    def __iter__(self):
        node = self
        while node:
            yield node.head
            node = node.tail
```

### 8.2 Why Decorators for Primitives?

Decorators provide:
- Declarative style (self-documenting)
- Automatic registration
- Validation injection (params, types)
- Introspection (doc, signature)

**Alternative:** Class-based approach for complex primitives:

```python
class JoyPrimitive:
    name: str
    params: int

    def validate(self, ctx): ...
    def execute(self, ctx): ...
```

### 8.3 Tail-Call Optimization

Python does not support tail-call optimization. Options:

1. **Trampoline Pattern:** Return thunks, execute in loop
2. **Exception-Based:** Raise `TailCall` exception, catch in main loop
3. **Recursion Limit:** Accept Python's ~1000 recursion limit
4. **Generator-Based:** Use generators for continuation-passing

**Recommended:** Trampoline for recursion combinators:

```python
class TailCall:
    def __init__(self, func, *args):
        self.func = func
        self.args = args

def trampoline(func, *args):
    result = func(*args)
    while isinstance(result, TailCall):
        result = result.func(*result.args)
    return result
```

### 8.4 Error Handling

Joy's C implementation uses `longjmp` for error recovery. Python options:

1. **Exceptions:** Natural fit for Python
2. **Result Types:** `Either[Error, Value]` pattern
3. **Global Error State:** Like C's `execerror`

**Recommended:** Python exceptions with custom types:

```python
class JoyError(Exception):
    """Base class for Joy errors"""
    pass

class JoyStackUnderflow(JoyError):
    pass

class JoyTypeError(JoyError):
    pass

class JoyUndefinedWord(JoyError):
    pass
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
import pytest

def test_dup():
    ctx = ExecutionContext()
    ctx.stack.push(42)
    dup(ctx)
    assert ctx.stack.depth == 2
    assert ctx.stack.peek(0).value == 42
    assert ctx.stack.peek(1).value == 42

def test_map():
    evaluator = Evaluator()
    evaluator.execute(parse("[1 2 3] [dup *] map"))
    result = evaluator.ctx.stack.peek()
    assert result.value == (1, 4, 9)

def test_linrec_factorial():
    evaluator = Evaluator()
    # factorial = [0 =] [pop 1] [dup 1 -] [*] linrec
    evaluator.execute(parse("5 [0 =] [pop 1] [dup 1 -] [*] linrec"))
    result = evaluator.ctx.stack.peek()
    assert result.value == 120
```

### 9.2 Compatibility Tests

Run original Joy test suite:

```python
def test_joy_compatibility():
    """Run tests from test2/*.joy"""
    for test_file in Path("test2").glob("*.joy"):
        source = test_file.read_text()
        result = run_joy(source)
        assert "false" not in result.lower()
```

---

## 10. Example Usage

### 10.1 Basic REPL

```python
from pyjoy import Evaluator, Scanner, Parser

def repl():
    evaluator = Evaluator()
    scanner = Scanner()
    parser = Parser()

    print("PyJoy REPL. Type 'quit' to exit.")
    while True:
        try:
            line = input("> ")
            if line.strip() == "quit":
                break

            tokens = scanner.tokenize(line)
            program = parser.parse(tokens)
            evaluator.execute(program)

            # Print stack
            print(f"Stack: {evaluator.ctx.stack}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    repl()
```

### 10.2 Python Extension Example

```python
from pyjoy import joy_word, ExecutionContext, JoyValue

# Define custom word that calls Python's math library
import math

@joy_word(name="sqrt", params=1, doc="N -> F")
def sqrt_word(ctx: ExecutionContext) -> None:
    """Square root using Python's math.sqrt"""
    n = ctx.stack.pop()
    result = math.sqrt(float(n.value))
    ctx.stack.push(JoyValue.floating(result))


@joy_word(name="http-get", params=1, doc="URL -> RESPONSE")
def http_get(ctx: ExecutionContext) -> None:
    """Fetch URL using Python's requests library"""
    import requests
    url = ctx.stack.pop()
    response = requests.get(url.value)
    ctx.stack.push(JoyValue.string(response.text))


# Usage in Joy:
# "https://api.example.com/data" http-get
```

### 10.3 Embedding in Python Application

```python
from pyjoy import Evaluator

def calculate_with_joy(expression: str) -> any:
    """Evaluate Joy expression and return result"""
    evaluator = Evaluator()
    evaluator.run(expression)
    return evaluator.ctx.stack.peek().value

# Example
result = calculate_with_joy("5 [0 =] [pop 1] [dup 1 -] [*] linrec")
print(f"5! = {result}")  # 5! = 120
```

---

## 11. Conclusion

Reimplementing Joy in Python offers several advantages:

1. **Extensibility:** Python functions become Joy words with simple decorators
2. **Interoperability:** Joy programs can leverage Python's ecosystem
3. **Maintainability:** Python code is more readable than C macros
4. **Portability:** Pure Python runs anywhere Python runs

Key challenges to address:

1. **Performance:** Python is ~10-100x slower than C
2. **Tail-Call Optimization:** Requires explicit handling (trampolines)
3. **Type Safety:** Runtime checks vs C's macro-based validation
4. **Memory:** Python objects have more overhead than C structs

The design prioritizes clarity and extensibility over raw performance, making PyJoy suitable for:
- Learning Joy language
- Rapid prototyping
- Embedding in Python applications
- Extending Joy with Python libraries

---

*Document version: 1.0*
*Last updated: 2026-01-01*
