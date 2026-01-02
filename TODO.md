# pyjoy - Status

## Current Test Results

**Python Interpreter:** 178/215 tests passing (82.8%)
**C Backend:** 199/215 tests passing (92.6%)
**pytest (unit tests):** 430/430 passing (100%)

Note: Recent fixes include inline definition processing (definitions now execute in order, not all upfront), set operations for and/or/xor/not, type preservation in map/filter, stack operation fixes, and type system updates.

---

## Remaining Tasks

### Missing Primitives (6)

| Primitive | Tests Affected | Description |
|-----------|---------------|-------------|
| `filetime` | 1 test | Get file modification time |
| `finclude` | 1 test | Include/execute Joy file at runtime |
| `id` | 1 test | Identity function (push symbol as-is) |
| `setecho` | 1 test | Set echo mode |
| `setsize` | 1 test | Set stack size limit |
| `__memoryindex` | 1 test | Memory index for gc |

### Bug Fixes Needed

These bugs were revealed when `.` started printing output:

1. **Float/Set bit-level equality** - `3.14159 {bits} =` expects IEEE 754 bit comparison (2 tests in eql.joy)

### File I/O Issues

8 tests fail because files can't be opened:
- `fclose.joy`, `feof.joy`, `ferror.joy`, `fgetch.joy`, `fgets.joy`, `fread.joy`, `fseek.joy`, `ftell.joy`
- These may be path resolution issues or missing test fixture files

### Other Categories

| Category | Count | Notes |
|----------|-------|-------|
| abort/quit behavior | 3 tests | Expected behavior (exit codes) |
| Interactive input | 1 test | `get.joy` needs stdin |

---

## Recently Completed

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
