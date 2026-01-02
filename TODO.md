# pyjoy C Backend - TODO

## Primitives Coverage

**Current: 201/203 (99%)** + 8 extensions

Run `uv run python scripts/check_c_coverage.py` for full report.

### Extensions (8)
- `.` / `newline` - Print newline
- `putln` - Put with newline
- `swoncat` - Swap then concat
- `condnestrec` - Conditional nested recursion
- `__settracegc` - Debug no-op
- `over` - X Y -> X Y X (copy second to top)
- `dup2` - X Y -> X Y X Y (duplicate top two)

---

## Remaining Primitives (2)

### Miscellaneous Commands (2)

| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `get` | `-> F` | Read factor from input |
| `include` | `"filnam.ext" ->` | Include Joy source file |

---

## Future Enhancements

### Compile-time `include` Support

Currently `include` cannot be meaningfully implemented as a runtime primitive in compiled code (no Joy parser available at runtime). To support `include`:

1. Modify the Python compiler/converter to detect `include` calls with string literals
2. Read and parse the included Joy source file at compile time
3. Inline the included definitions into the generated C code
4. Handle recursive includes and circular dependency detection

This would allow Joy programs using `include` to compile correctly.

---

## Recently Completed

- [x] Stack variants: `rollupd`, `rolldownd`, `rotated`
- [x] Type predicates: `leaf`, `file`
- [x] Arity combinators: `nullary`, `unary`, `binary`, `ternary`
- [x] Control flow: `cleave`
- [x] Type conditionals: `ifinteger`, `ifchar`, `iflogical`, `ifset`, `ifstring`, `iflist`, `iffloat`, `iffile`
- [x] Aggregate combinators: `some`, `all`, `split`, `enconcat`
- [x] System interaction: `system`, `getenv`, `argc`, `argv`
- [x] File I/O: `fopen`, `fclose`, `fflush`, `feof`, `ferror`, `fgetch`, `fgets`, `fread`, `fput`, `fputch`, `fputchars`, `fputstring`, `fwrite`, `fseek`, `ftell`, `fremove`, `frename`
- [x] Application combinators: `app1`, `app11`, `app12`, `app2`, `app3`, `app4`
- [x] Interpreter control: `abort`, `quit`, `gc`, `setautoput`, `setundeferror`, `autoput`, `undeferror`, `echo`, `conts`, `undefs`
- [x] Help system: `help`, `helpdetail`, `manual`

---

## Priority

### High (commonly used)
- [x] ~~`some`, `all` - aggregate predicates~~
- [x] ~~`nullary`, `unary`, `binary`, `ternary` - arity combinators~~
- [x] ~~`cleave` - parallel application~~
- [x] ~~`leaf`, `file` - type predicates~~
- [x] ~~File I/O: `fopen`, `fclose`, `fread`, `fwrite`, `fgets`~~
- [x] ~~`system`, `getenv`, `argv`, `argc` - system interaction~~

### Medium
- [x] ~~Type conditionals (`ifinteger`, `ifchar`, etc.)~~
- [x] ~~Application combinators (`app1`, `app2`, etc.)~~
- [x] ~~Arity combinators (`unary2`, `unary3`, `unary4`)~~
- [x] ~~Control flow (`construct`)~~
- [x] ~~Time operations (`localtime`, `gmtime`, `mktime`, `strftime`)~~
- [x] ~~Tree combinators (`treestep`, `treerec`, `treegenrec`)~~
- [x] ~~Predicate (`user`)~~

### Low (interpreter-specific)
- [x] ~~`help`, `helpdetail`, `manual`~~
- [x] ~~`conts`, `autoput`, `undeferror`, `echo`~~
- [x] ~~`gc`, `abort`, `quit`~~

---

## Test Status

**jp-nestrec.joy: PASSING** - All tests run successfully.

### Working Tests

| Test | Combinator | Status |
|------|------------|--------|
| r-fact | ifte | PASS |
| r-mcc91 | ifte | PASS |
| r-ack | cond | PASS |
| r-hamilhyp | ifte | PASS |
| x-fact | x | PASS |
| x-mcc91 | x | PASS |
| x-ack | x | PASS |
| y-ack | y | PASS |
| x-hamilhyp | x | PASS |
| l-mcc91 | linrec | PASS |
| l-ack | linrec | PASS |
| lr-hamilhyp | linrec | PASS |
| toggle | ifte | PASS |
| lr-grayseq | linrec | PASS |
| cnr-hamilhyp | condnestrec | PASS |
| cnr-ack | condnestrec | PASS |
| cnr-grayseq | condnestrec | PASS |
| cnr-hanoi | condnestrec | PASS |
| cnr-fact | condnestrec | PASS |
| cnr-mcc91 | condnestrec | PASS |
| cnr-even | condnestrec | PASS |
| cnr-abs | condnestrec | PASS |

### Test Commands

```bash
# Compile and run jp-nestrec.joy
uv run python -m pyjoy compile tests/examples/jp-nestrec.joy -o build -n jp-nestrec && ./build/jp-nestrec

# Run official Joy tests
uv run python -m pyjoy compile joy/test2/condlinrec.joy -o build -n test && ./build/test
```
