# pyjoy - Status

## Current Test Results

**Python Interpreter:** 194/215 tests passing (90.2%)
**C Backend:** 199/215 tests passing (92.6%)
**pytest (unit tests):** 430/430 passing (100%)

Note: Recent fixes include `case` combinator (default case semantics), Float/SET bit-level equality (IEEE 754), iterative linrec combinator, and new primitives.

---

## Remaining Tasks

### Known Issues

| Test | Issue |
|------|-------|
| condlinrec.joy, condnestrec.joy | Conditional recursion combinator bugs |
| app11.joy | app11 not consuming all expected args |
| treestep.joy | Tree step combinator issue |
| argc.joy, argv.joy | Command-line argument test environment mismatch |

### Test Categories (Non-Bug)

| Category | Count | Notes |
|----------|-------|-------|
| abort/quit behavior | 3 tests | Expected behavior (intentional exit codes) |
| Interactive input | 1 test | `get.joy` needs stdin |
| Documentation output | 3 tests | help.joy, manual.joy, undefs.joy - output format |

---

## Recently Completed

- [x] `case` combinator - Fixed default case semantics (last clause is always default, X preserved)
- [x] Float/SET bit-level equality - `3.14159 {bits} =` now compares IEEE 754 bit representation
- [x] Iterative `linrec` combinator - Prevents Python stack overflow with deep recursion (e.g., `from-to-list 1 14000`)
- [x] `filetime` primitive - Get file modification time as epoch integer
- [x] `finclude` primitive - Include/execute Joy file at runtime (silent on missing files)
- [x] `id` primitive - Identity function (no-op)
- [x] `setecho`/`echo` primitives - Set and get echo mode
- [x] `setautoput`/`autoput` primitives - Set and get autoput mode
- [x] `setsize` primitive - Returns max set size (64)
- [x] `__memoryindex`/`__memorymax` primitives - Memory tracking stubs for GC tests
- [x] File I/O path fixes - Updated test files to use full paths; fixed `fseek` to return `S B` (stream + boolean) (8 tests)
- [x] `$` shell escape - Lines starting with `$` at column 0 execute rest of line as shell command (7 tests)
- [x] Inline definition processing - DEFINE/LIBRA blocks are now processed in order as code executes, not all upfront (fixes cond.joy and other tests that redefine words)
- [x] `and`/`or`/`xor`/`not` - now handle SETs as set operations (intersection/union/symmetric diff/complement)
- [x] `map`/`filter`/`split` - preserve STRING and SET types (was always returning LIST)
- [x] `_make_aggregate` - convert integers to chars when reconstructing strings
- [x] `rotate` - fixed to `X Y Z -> Z Y X` (flip first and third)
- [x] `rotated`/`rollupd`/`rolldownd` - fixed stack operations
- [x] `unstack` - now pushes in reverse order (TOS-first list order)
- [x] `infra` - fixed stack order (TOS-first for input and output)
- [x] `list` predicate - now returns true for QUOTATION as well as LIST
- [x] `some` combinator - empty predicate now tests item truthiness
- [x] `name` - returns Joy type name strings for non-symbols
- [x] `typeof` - updated to Joy42 type codes (2=USRDEF, 3=BUILTIN, 4=BOOLEAN, etc.)
- [x] `_execute_term` - symbol JoyValues now execute instead of being pushed
- [x] `.` (period) operator - now prints TOS with newline (no-op if stack empty)
- [x] Octal character escapes in scanner (`'\010` etc.)
- [x] `equal` in C runtime - LIST/QUOTATION comparison by content
- [x] `stack` primitive - returns items with TOS first
- [x] CONST keyword support in parser
- [x] `-name` symbols (like `-inf`) in scanner
- [x] `ldexp` overflow handling (returns infinity)
- [x] C test build directory structure (`build/<stem>/`)
- [x] `condlinrec` combinator
- [x] `cleave` combinator (fixed signature)
- [x] `construct` combinator (fixed to push individual results)
- [x] `primrec` combinator (fixed semantics)
- [x] `treerec` / `treegenrec` combinators
- [x] `opcase` combinator (match by type)
- [x] `pick` primitive (pick from stack)
- [x] `unassign` primitive
- [x] `undeferror` / `setundeferror` primitives
- [x] `format` precision handling for integers

---

## Test Commands

```bash
# Run Python interpreter tests
uv run pyjoy test tests/joy

# Run with C compilation
uv run pyjoy test tests/joy --compile

# Run specific pattern
uv run pyjoy test tests/joy --pattern "*.joy" -v

# Compile single file
uv run pyjoy compile tests/joy/example.joy --run
```

---

## Architecture Notes

### `.` Operator Behavior

The `.` (period) operator now:
1. Prints TOS with newline if stack is not empty
2. Does nothing (no-op) if stack is empty
3. Is parsed as a symbol in executable code
4. Still ends DEFINE/LIBRA blocks in definition context

### C Build Structure

When running `pyjoy test --compile`, each Joy file compiles to:
```
build/
  <filename>/
    <filename>.c
    <filename>      (executable)
    Makefile
    joy_runtime.c
    joy_runtime.h
    joy_primitives.c
```
