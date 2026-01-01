# pyjoy C Backend - TODO

## Primitives Coverage

**Current: 196/203 (96%)** + 8 extensions

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

## Remaining Primitives (7)

### Operand (2)

| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `conts` | `-> [[P] [Q] ..]` | Push continuation stack |
| `undefs` | `->` | Push list of undefined symbols |

### Miscellaneous Commands (5)

| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `help` | `->` | Display help |
| `helpdetail` | `[S1 S2 ..] ->` | Display detailed help for symbols |
| `manual` | `->` | Display full manual |
| `get` | `-> F` | Read factor from input |
| `include` | `"filnam.ext" ->` | Include Joy source file |

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
- [ ] `help`, `helpdetail`, `manual`
- [ ] `conts`, `autoput`, `undeferror`, `echo`
- [ ] `gc`, `abort`, `quit`

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
