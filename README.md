# pyjoy

Towards a python implementation of Manfred von Thun's Joy Language.

The primary aim of this project is to [implement the Joy language in python3](docs/pyjoy.md). The means that the implementation should run joy programs without issue. A secondary aim is to have the python implementation generate c code which can then be compiled into machine code. This is consistent with the late Manfred von Thun's wish:

> Several other people have published other more or less complete Joy
> interpreters, written in ML and in Scheme, in the "concatenative" mailing group.
> At this point in time I have no plans to write a full compiler.  A first
> version of such a compiler would presumably use C as an intermediate language
> and leave the generation of machine code to the C compiler.  I would very much
> welcome if somebody were to take up the task." [A Conversation with Manfred von Thun](https://www.nsl.com/papers/interview.htm)

There's also a sister [pyjoy2](https://github.com/shakfu/pyjoy2) project which has the different aim of Pythonically re-imagining the Joy language, without adherence to the requirement of running existing Joy programs.

## Building

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
# Clone the repository
git clone https://github.com/shakfu/pyjoy.git
cd pyjoy

# Install dependencies
make sync

# Run tests
make test

# Check code quality
make lint
make typecheck
```

For C compilation, you'll also need `gcc` or `clang`.

## Usage

### Interactive REPL

```bash
# Start the Joy REPL
make repl
# or
uv run python -m pyjoy
```

Example session:
```
Joy> 2 3 + .
5
Joy> [1 2 3] [dup *] map .
[1 4 9]
Joy> quit
```

### Execute Joy Files

```bash
# Run a Joy source file
uv run python -m pyjoy examples/factorial.joy

# Evaluate an expression
uv run python -m pyjoy -e "5 [1] [*] primrec ."
```

### Compile to C

```bash
# Compile Joy source to executable
uv run python -m pyjoy compile program.joy -o build -n myprogram

# Run the compiled program
./build/myprogram

# Or compile and run in one step
uv run python -m pyjoy compile program.joy -o build -n myprogram --run
```

## Status

- **C Backend Coverage:** 125/203 primitives (61%) + 8 extensions
- **Python Interpreter:** Full Joy language support
- **Compilation:** Joy source to C executable via `pyjoy compile`
- **Tests:** 411 pytest tests passing

### Recent Additions

- Aggregate combinators: `split`, `enconcat`
- File I/O: `stdin`, `stdout`, `stderr` (JOY_FILE type support)
- Math primitives: `acos`, `asin`, `atan`, `atan2`, `cosh`, `sinh`, `tanh`, `log10`, `frexp`, `ldexp`, `modf`
- String conversion: `strtol`, `strtod`
- Time/random: `time`, `clock`, `rand`, `srand`
- Recursive combinators: `condlinrec`, `condnestrec`, `linrec`, `genrec`, `primrec`
- Aggregate operations: `unswons`, `of`, `at`, `drop`, `take`, `in`, `compare`, `equal`
- Set operations: `xor`, `and`, `or`, `not` (with proper set semantics)
- Symbol operations: `name`, `intern`, `body`
- Constants: `maxint`, `setsize`

Run `uv run python scripts/check_c_coverage.py` for the full coverage report.
