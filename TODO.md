# pyjoy - Status

## Current Test Results

**Python Interpreter:** 209/215 tests passing (97.2%)
**C Backend:** 198/215 tests passing (92.1%)
**pytest (unit tests):** 712/712 passing (100%)

Note: Recent fixes include `inf`/`-inf` float literals, bit-level INT->FLOAT casting, `strtol` base-0 detection, test runner false positive fix, C backend INFINITY/NAN support.

---

## Remaining Tasks

### Known Issues

| Test | Issue |
|------|-------|
| maxint.joy | Python arbitrary precision differs from Joy64 fixed 64-bit overflow |
| mktime.joy | Time function format/behavior differences |

### Test Categories (Non-Bug)

| Category | Count | Notes |
|----------|-------|-------|
| abort/quit behavior | 4 tests | Expected behavior (intentional exit codes) |
| Interactive input | 1 test | `get.joy` needs stdin |

---

## Recently Completed

- [x] `inf`/`-inf`/`nan` literals - Scanner now recognizes special float literals (with word boundary and definition lookahead)
- [x] `casting` INT->FLOAT - Now uses bit-level reinterpretation (treats integer bits as IEEE 754 double)
- [x] `strtol` base-0 - Auto-detects hex (0x prefix) and octal (0 prefix) like C
- [x] `sametype` for builtins - Two builtin symbols only sametype if same name
- [x] `fflush` / FILE equality - Added FILE comparison to `_joy_equals`
- [x] `argc`/`argv` primitives - Now use Joy-specific argv (just the Joy filename when running a file)
- [x] `autoput` default - Changed from 0 to 1 (enabled by default, matching Joy42)
- [x] `equal` function - Now compares symbols and strings by their text content
- [x] `casting` primitive - Fixed type codes to match Joy42 `typeof` codes
- [x] `app11` combinator - Fixed to clear stack before applying quotation to X and Y
- [x] `treestep` combinator - Fixed to handle JoyQuotation objects in tree structure
- [x] `condlinrec` combinator - Fixed clause handling for JoyQuotation types
- [x] `condnestrec` combinator - Unified with condlinrec (same semantics as C runtime)
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
