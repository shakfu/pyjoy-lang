# PyJoy Overview

A Python 3.13+ implementation of Manfred von Thun's Joy programming language with dual-mode architecture and C code generation.

## Goals

1. **Faithful Joy Semantics** - Preserve the concatenative, stack-based execution model
2. **Dual-Mode Architecture** - Strict mode for Joy compliance, pythonic mode for Python integration
3. **Python Extensibility** - Define new Joy words as Python functions
4. **C Code Generation** - Compile Joy programs to standalone executables

## Architecture

```
Source Code
     |
     v
+-----------+     +----------+     +-----------+
|  Scanner  | --> |  Parser  | --> | Evaluator |
| (tokens)  |     |  (AST)   |     |  (stack)  |
+-----------+     +----------+     +-----------+
                                         |
                       +-----------------+-----------------+
                       |                                   |
                       v                                   v
              +----------------+                  +----------------+
              | Python Backend |                  |   C Backend    |
              | (interpreter)  |                  | (code gen)     |
              +----------------+                  +----------------+
```

### Module Structure

```
src/pyjoy/
    __init__.py         # Public API
    scanner.py          # Lexical analysis
    parser.py           # AST construction
    types.py            # Joy type system (JoyValue, JoyQuotation)
    stack.py            # Stack and ExecutionContext
    evaluator/          # Python interpreter
        core.py         # Evaluator class, decorators
        arithmetic.py   # +, -, *, /, math functions
        combinators.py  # ifte, map, filter, linrec, binrec
        stack_ops.py    # dup, swap, pop, etc.
        aggregate.py    # List/string/set operations
        io.py           # File and console I/O
    backends/c/         # C code generator
        converter.py    # Joy AST to C AST
        emitter.py      # C code emission
        builder.py      # Compilation driver
        runtime/        # C runtime library
```

## Type System

Joy values are represented as tagged unions:

| Joy Type | Python Representation | Notes |
|----------|----------------------|-------|
| INTEGER | `int` | Arbitrary precision |
| FLOAT | `float` | IEEE 754 double |
| STRING | `str` | UTF-8 |
| CHAR | `str` (len 1) | Single character |
| BOOLEAN | `bool` | `true` / `false` |
| LIST | `tuple` | Immutable |
| SET | `frozenset` | Members restricted to 0-63 |
| FILE | file object | I/O handles |
| QUOTATION | `JoyQuotation` | Unevaluated code `[...]` |

In strict mode, all stack values are wrapped in `JoyValue`. In pythonic mode, raw Python objects can also live on the stack.

## Dual-Mode Architecture

PyJoy supports two execution modes controlled by the `strict` parameter:

### Strict Mode (`strict=True`, default)

- All values wrapped in `JoyValue` tagged unions
- Exact Joy type semantics
- No Python interop syntax
- Use for Joy compliance and compatibility testing

```python
from pyjoy import Evaluator

ev = Evaluator(strict=True)
ev.run("5 dup *")
result = ev.stack.pop()  # JoyValue(type=INTEGER, value=25)
```

### Pythonic Mode (`strict=False`)

- Any Python object can live on the stack
- Python interop syntax enabled (backticks, `$()`, `!`)
- Pre-imported modules available
- Use for Python integration and scripting

```python
ev = Evaluator(strict=False)
ev.run("`[x**2 for x in range(5)]`")  # Push Python list
ev.run("[3 <] filter")                 # Use Joy combinators
```

**Python Interop Syntax:**

| Syntax | Description | Example |
|--------|-------------|---------|
| `` `expr` `` | Evaluate Python, push result | `` `math.sqrt(16)` `` |
| `$(expr)` | Alternative syntax | `$(len([1,2,3]))` |
| `!stmt` | Execute Python statement | `!x = 42` |

**Pre-imported modules:** `math`, `json`, `os`, `sys`, `re`, `itertools`, `functools`, `collections`

See [pythonic-mode.md](pythonic-mode.md) for the complete guide.

## Extending Joy from Python

Two decorators are provided for defining new Joy words:

### `@python_word` - Simple Functions

For pure functions with fixed arity and single return value:

```python
from pyjoy.evaluator import python_word

@python_word(name="hypot", doc="X Y -> Z")
def hypot(x, y):
    return (x**2 + y**2) ** 0.5
```

The decorator automatically:
- Pops arguments from stack
- Unwraps `JoyValue` to raw Python values
- Wraps result back to `JoyValue` (in strict mode)
- Pushes result (if not `None`)

### `@joy_word` - Full Stack Control

For words needing direct stack access, multiple results, or complex control flow:

```python
from pyjoy.evaluator import joy_word, ExecutionContext

@joy_word(name="dup2", params=2, doc="X Y -> X Y X Y")
def dup2(ctx: ExecutionContext):
    y, x = ctx.stack.pop_n(2)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)
```

### Mode-Aware Helpers

For primitives that need to work in both modes:

```python
from pyjoy.evaluator import unwrap_value, wrap_value, get_numeric

# Extract raw value from JoyValue or pass through
raw = unwrap_value(stack_value)

# Wrap result appropriately for current mode
result = wrap_value(42, strict=ctx.strict)

# Get numeric value from either JoyValue or raw Python
num = get_numeric(value)  # Works with int, float, bool, char
```

## C Backend

PyJoy can compile Joy programs to standalone C executables.

### Usage

```bash
# Compile to executable
uv run pyjoy compile program.joy -o build -n myprogram

# Compile and run
uv run pyjoy compile program.joy --run

# Generate C code only
uv run pyjoy compile program.joy --no-compile
```

### Architecture

```
Joy Source
     |
     v
+-----------+
|  Parser   |  (same as interpreter)
+-----------+
     |
     v
+-----------+     +----------+     +----------+
| Converter | --> | Emitter  | --> |  gcc/    |
| (Joy->C)  |     | (C code) |     |  clang   |
+-----------+     +----------+     +----------+
     |                                   |
     v                                   v
+----------------+              +------------+
| C Runtime      |   linked     | Executable |
| (joy_runtime.c)|   with       |            |
+----------------+              +------------+
```

### Features

- **Compile-time include processing** - `include` directives resolved at compile time
- **Circular dependency detection** - Prevents infinite include loops
- **Full runtime** - ~140KB C runtime with garbage collection
- **Standard primitives** - 200+ primitives implemented in C

### Limitations

- Some interpreter-specific primitives (`get`, interactive I/O) have limited support
- Python interop not available in compiled output
- Reflection primitives (`body`, `name`) work differently

## Key Implementation Details

### Quotations

Quotations `[...]` are first-class values representing unevaluated code:

```python
class JoyQuotation:
    def __init__(self, terms: tuple):
        self.terms = terms  # Sequence of literals and symbols
```

Combinators like `i`, `map`, `ifte` execute quotations on the stack.

### Recursion Combinators

Joy's recursion combinators (`linrec`, `binrec`, `primrec`, `genrec`) are implemented using Python's call stack with explicit stack state management:

```
linrec: [P] [T] [R1] [R2] ->
  if P then T
  else R1; recurse; R2

binrec: [P] [T] [R1] [R2] ->
  if P then T
  else R1 (split); recurse on both; R2 (merge)
```

### Error Handling

Custom exception hierarchy:

- `JoyError` - Base class
- `JoyStackUnderflow` - Not enough values on stack
- `JoyTypeError` - Wrong type for operation
- `JoyUndefinedWord` - Unknown word
- `JoyDivisionByZero` - Division by zero

## Testing

```bash
# Python unit tests (712 tests)
make test

# Joy language compliance tests (215 .joy files)
make test-joy

# Joy tests with C compilation
uv run pyjoy test tests/joy --compile
```

### Test Results

| Backend | Passing | Total | Coverage |
|---------|---------|-------|----------|
| Python Interpreter | 194 | 215 | 90.2% |
| C Backend | 199 | 215 | 92.6% |
| pytest (unit) | 712 | 712 | 100% |

## Performance Notes

The Python interpreter prioritizes clarity over speed:

- ~10-100x slower than C implementation
- Acceptable for interactive use and development
- Use C backend for performance-critical applications

For computationally intensive Joy programs, compile to C.

## Related Documentation

- [Pythonic Mode Guide](pythonic-mode.md) - Python integration features
- [Comparison with Joy](comparison-with-joy.md) - Word-by-word comparison
- [Tutorial](tutorial.md) - Getting started with Joy
- [Rationale for Joy](rationale-for-joy.md) - Why concatenative programming?

## References

- [Joy Language Home](http://www.latrobe.edu.au/humanities/research/research-projects/past-projects/joy-programming-language)
- [A Conversation with Manfred von Thun](https://www.nsl.com/papers/interview.htm)
- [Joy42](https://github.com/Wodan58/Joy) - Reference C implementation
