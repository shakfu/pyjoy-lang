# pyjoy - Status

## Current Test Results

**Python Interpreter:** 154/215 tests passing (71.6%)
**C Backend:** 190/215 tests passing (88.4%)

Note: The Python test count dropped from 186 after fixing the `.` (period) operator to actually print output. This revealed ~45 tests that were silently outputting `false` due to bugs in primitives.

---

## Remaining Tasks

### Missing Primitives (7)

| Primitive | Tests Affected | Description |
|-----------|---------------|-------------|
| `$` | 7 tests | String format/interpolation operator |
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
