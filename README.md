# pyjoy

A Python implementation of Manfred von Thun's Joy programming language.

The primary aim of this project is to [implement the Joy language in Python 3](docs/pyjoy.md). This means the implementation should run Joy programs without issue. A secondary aim is to have the Python implementation generate C code which can then be compiled into machine code. This is consistent with the late Manfred von Thun's wish:

> Several other people have published other more or less complete Joy
> interpreters, written in ML and in Scheme, in the "concatenative" mailing group.
> At this point in time I have no plans to write a full compiler. A first
> version of such a compiler would presumably use C as an intermediate language
> and leave the generation of machine code to the C compiler. I would very much
> welcome if somebody were to take up the task." [A Conversation with Manfred von Thun](https://www.nsl.com/papers/interview.htm)

There's also a sister [pyjoy2](https://github.com/shakfu/pyjoy2) project which has the different aim of Pythonically re-imagining the Joy language, without adherence to the requirement of running existing Joy programs.

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
```
Joy> 2 3 + .
5
Joy> [1 2 3] [dup *] map .
[1 4 9]
Joy> DEFINE square == dup *.
Joy> 5 square .
25
Joy> quit
```

### Execute Joy Files

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
|---------|---------|-------|----------|
| Python Interpreter | 154 | 215 | 71.6% |
| C Backend | 190 | 215 | 88.4% |
| pytest (unit tests) | 420 | 420 | 100% |

### Primitives

- **200+ primitives** implemented in both Python and C backends
- Full support for Joy's core operations, combinators, and I/O
- Some interpreter-specific primitives (`get`, `include`) have limited C support

### Missing Primitives (7)

| Primitive | Description |
|-----------|-------------|
| `$` | String format/interpolation |
| `filetime` | File modification time |
| `finclude` | Runtime file include |
| `id` | Identity (push symbol) |
| `setecho` | Set echo mode |
| `setsize` | Set stack size |
| `__memoryindex` | Memory index for gc |

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

### C Backend Features

- Compiles Joy to standalone C executables
- Compile-time `include` preprocessing
- Recursive include with circular dependency detection
- Full runtime with garbage collection

## Project Structure

```
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
```

## License

MIT License - see LICENSE file for details.

## References

- [Joy Language Home](http://www.latrobe.edu.au/humanities/research/research-projects/past-projects/joy-programming-language)
- [A Conversation with Manfred von Thun](https://www.nsl.com/papers/interview.htm)
- [Joy42](https://github.com/Wodan58/Joy) - Reference C implementation
