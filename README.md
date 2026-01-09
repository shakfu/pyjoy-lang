# pyjoy

A Python implementation of Manfred von Thun's Joy programming language with dual-mode architecture.

The primary aim of this project is to [implement the Joy language in Python 3](docs/pyjoy.md). This means the implementation should run Joy programs without issue. A secondary aim is to have the Python implementation generate C code which can then be compiled into machine code. This is consistent with the late Manfred von Thun's wish:

> Several other people have published other more or less complete Joy
> interpreters, written in ML and in Scheme, in the "concatenative" mailing group.
> At this point in time I have no plans to write a full compiler. A first
> version of such a compiler would presumably use C as an intermediate language
> and leave the generation of machine code to the C compiler. I would very much
> welcome if somebody were to take up the task." [A Conversation with Manfred von Thun](https://www.nsl.com/papers/interview.htm)

The implementation provides a **dual-mode architecture**: strict mode (`strict=True`) for Joy compliance, and pythonic mode (`strict=False`) for Python interoperability.

## Building

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
# Clone the repository
git clone https://github.com/shakfu/pyjoy.git
cd pyjoy

# Install dependencies
uv sync

# Run Python tests
uv run pytest

# Run Joy test suite
uv run pyjoy test tests/joy

# Run Joy tests with C compilation
uv run pyjoy test tests/joy --compile
```

For C compilation, you'll also need `gcc` or `clang`.

## Usage

### Interactive REPL

```bash
# Start the Joy REPL
uv run pyjoy
```

Example session:

```text
Joy> 2 3 + .
5
Joy> [1 2 3] [dup *] map .
[1 4 9]
Joy> DEFINE square == dup *.
Joy> 5 square .
25
Joy> quit
```

### Execute Joy files

```bash
# Run a Joy source file
uv run pyjoy examples/factorial.joy

# Or using the run subcommand
uv run pyjoy run examples/factorial.joy

# Evaluate an expression
uv run pyjoy -e "5 [1] [*] primrec ."
120
```

### Compile to C

```bash
# Compile Joy source to executable
uv run pyjoy compile program.joy -o build -n myprogram

# Run the compiled program
./build/myprogram

# Or compile and run in one step
uv run pyjoy compile program.joy --run

# Generate C code only (no compilation)
uv run pyjoy compile program.joy --no-compile
```

### Run Test Suite

```bash
# Run all Joy tests
uv run pyjoy test tests/joy

# Run with verbose output
uv run pyjoy test tests/joy -v

# Run specific pattern
uv run pyjoy test tests/joy --pattern "fact*.joy"

# Also test C compilation
uv run pyjoy test tests/joy --compile
```

## Status

### Test Results

| Backend | Passing | Total | Coverage |
| ------- | ------- | ----- | -------- |
| Python Interpreter | 194 | 215 | 90.2% |
| C Backend | 199 | 215 | 92.6% |
| pytest (unit tests) | 712 | 712 | 100% |

### Primitives

- **200+ primitives** implemented in both Python and C backends
- Full support for Joy's core operations, combinators, and I/O
- Mode-aware primitives work with both strict (JoyValue) and pythonic (raw Python) values
- Some interpreter-specific primitives (`get`, `include`) have limited C support

See [TODO.md](TODO.md) for detailed status and remaining work.

## Features

### Core Language

- Stack operations: `dup`, `pop`, `swap`, `rollup`, `rolldown`, `rotate`, etc.
- Arithmetic: `+`, `-`, `*`, `/`, `rem`, `div`, `abs`, `neg`, `sign`, etc.
- Comparison: `<`, `>`, `<=`, `>=`, `=`, `!=`, `equal`, `compare`
- Logic: `and`, `or`, `not`, `xor`
- Aggregates: lists `[...]`, sets `{...}`, strings `"..."`
- Quotations and combinators

### Combinators

- Basic: `i`, `x`, `dip`, `dipd`, `dipdd`
- Conditionals: `ifte`, `cond`, `branch`, `iflist`, `ifinteger`, etc.
- Recursion: `linrec`, `binrec`, `genrec`, `primrec`, `tailrec`
- Tree recursion: `treerec`, `treegenrec`, `treestep`
- Conditional recursion: `condlinrec`, `condnestrec`
- Application: `app1`, `app2`, `app3`, `app4`, `map`, `filter`, `fold`, `step`
- Arity: `nullary`, `unary`, `binary`, `ternary`, `unary2`, `unary3`, `unary4`
- Control: `cleave`, `construct`, `some`, `all`, `split`

### I/O and System

- Console: `put`, `putch`, `putchars`, `.` (print with newline)
- File I/O: `fopen`, `fclose`, `fread`, `fwrite`, `fgets`, `fput`, etc.
- System: `system`, `getenv`, `argc`, `argv`
- Time: `time`, `localtime`, `gmtime`, `mktime`, `strftime`

### Python Interop (Pythonic Mode)

When running with `strict=False`, Joy gains Python interoperability:

```python
from pyjoy import Evaluator

ev = Evaluator(strict=False)  # Enable pythonic mode

# Backtick expressions - evaluate Python and push result
ev.run("`2 + 3`")           # Pushes 5
ev.run("`math.sqrt(16)`")   # Pushes 4.0 (math is pre-imported)

# Dollar expressions - same as backticks, better for nested parens
ev.run("$(len([1,2,3]))")   # Pushes 3

# Bang statements - execute Python without pushing
ev.run("!x = 42")           # Sets x in Python namespace
ev.run("`x * 2`")           # Pushes 84

# Access stack from Python
ev.run("1 2 3")
ev.run("`sum(stack)`")      # Pushes 6

# Define Python functions
ev.run("!def square(n): return n * n")
ev.run("`square(7)`")       # Pushes 49
```

**Pre-imported modules**: `math`, `json`, `os`, `sys`, `re`, `itertools`, `functools`, `collections`

**Available in namespace**: `stack` (alias `S`), `ctx`, `evaluator`

See [docs/pythonic-mode.md](docs/pythonic-mode.md) for the complete guide.

### Extending Joy from Python

Define new Joy words using Python decorators:

```python
from pyjoy.evaluator import joy_word, python_word, ExecutionContext
from pyjoy.types import JoyValue

# Simple functions: use @python_word (auto-pops args, pushes result)
@python_word(name="hypot", doc="X Y -> Z")
def hypot(x, y):
    return (x**2 + y**2) ** 0.5

# Full stack control: use @joy_word
@joy_word(name="rot3", params=3, doc="X Y Z -> Y Z X")
def rot3(ctx: ExecutionContext):
    c, b, a = ctx.stack.pop_n(3)
    ctx.stack.push_value(b)
    ctx.stack.push_value(c)
    ctx.stack.push_value(a)

# Wrap existing Python functions
import math

@python_word(name="deg2rad")
def deg2rad(degrees):
    return math.radians(degrees)

@python_word(name="factorial")
def factorial(n):
    return math.factorial(int(n))
```

**When to use each decorator:**

| Decorator | Use When |
|-----------|----------|
| `@python_word` | Pure functions, fixed arity, single return value |
| `@joy_word` | Need stack access, multiple results, control flow, or `ExecutionContext` |

**Example: HTTP fetch word**

```python
@joy_word(name="http-get", params=1, doc="URL -> RESPONSE")
def http_get(ctx: ExecutionContext):
    import requests
    url = ctx.stack.pop()
    response = requests.get(url.value if hasattr(url, 'value') else url)
    ctx.stack.push(response.text)
```

### C Backend Features

- Compiles Joy to standalone C executables
- Compile-time `include` preprocessing
- Recursive include with circular dependency detection
- Full runtime with garbage collection

## Project Structure

```sh
pyjoy/
  src/pyjoy/
    __init__.py         # Public API
    __main__.py         # CLI entry point
    types.py            # Joy type system
    stack.py            # Stack implementation
    scanner.py          # Lexical analysis
    parser.py           # Parser
    evaluator/          # Execution engine
    backends/c/         # C code generator
    stdlib/             # Joy standard library
  tests/
    joy/                # Joy language tests
    test_*.py           # pytest unit tests
  docs/
    pyjoy.md            # Implementation spec
    pythonic-mode.md    # Python integration guide
    comparison-with-joy.md  # Word comparison tables
    tutorial.md         # Getting started
```

## Documentation

- [Implementation Spec](docs/pyjoy.md) - Architecture and design
- [Pythonic Mode Guide](docs/pythonic-mode.md) - Python integration features
- [Comparison with Joy](docs/comparison-with-joy.md) - Word-by-word comparison
- [Tutorial](docs/tutorial.md) - Getting started with Joy

## License

MIT License - see LICENSE file for details.

## References

- [Joy Language Home](http://www.latrobe.edu.au/humanities/research/research-projects/past-projects/joy-programming-language)
- [A Conversation with Manfred von Thun](https://www.nsl.com/papers/interview.htm)
- [Joy42](https://github.com/Wodan58/Joy) - Reference C implementation
