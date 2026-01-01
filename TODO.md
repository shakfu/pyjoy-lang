# pyjoy C Backend - TODO

## Primitives Coverage

**Current: 172/203 (84%)** + 8 extensions

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

## Remaining Primitives (31)

### Operand (5)

| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `conts` | `-> [[P] [Q] ..]` | Push continuation stack |
| `autoput` | `-> I` | Push autoput flag value |
| `undeferror` | `-> I` | Push undeferror flag value |
| `undefs` | `->` | Push list of undefined symbols |
| `echo` | `-> I` | Push echo flag value (0..3) |

### Operator (8)

#### Time Operations
| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `localtime` | `I -> T` | Convert time_t to local time struct |
| `gmtime` | `I -> T` | Convert time_t to UTC time struct |
| `mktime` | `T -> I` | Convert time struct to time_t |
| `strftime` | `T S1 -> S2` | Format time as string |

#### Formatting
| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `format` | `N C I J -> S` | Format integer N with char C, width I, precision J |
| `formatf` | `F C I J -> S` | Format float F with char C, width I, precision J |

#### Case/Switch
| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `opcase` | `X [..[X Xs]..] -> [Xs]` | Case with quotation result |
| `case` | `X [..[X Y]..] -> Y i` | Case with immediate execution |

### Predicate (1)

| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `user` | `X -> B` | Test if X is user-defined |

### Combinator (7)

#### Arity Combinators
| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `unary2` | `X1 X2 [P] -> R1 R2` | Execute P on X1 and X2 separately |
| `unary3` | `X1 X2 X3 [P] -> R1 R2 R3` | Execute P on three values |
| `unary4` | `X1 X2 X3 X4 [P] -> R1 R2 R3 R4` | Execute P on four values |

#### Control Flow
| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `construct` | `[P] [[P1] [P2] ..] -> R1 R2 ..` | Execute P, then each Pi |

#### Tree Combinators
| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `treestep` | `T [P] -> ...` | Step through tree T with P |
| `treerec` | `T [O] [C] -> ...` | Tree recursion |
| `treegenrec` | `T [O1] [O2] [C] -> ...` | General tree recursion |

### Miscellaneous Commands (10)

| Primitive | Signature | Description |
|-----------|-----------|-------------|
| `help` | `->` | Display help |
| `helpdetail` | `[S1 S2 ..] ->` | Display detailed help for symbols |
| `manual` | `->` | Display full manual |
| `setautoput` | `I ->` | Set autoput flag |
| `setundeferror` | `I ->` | Set undeferror flag |
| `gc` | `->` | Force garbage collection |
| `get` | `-> F` | Read factor from input |
| `include` | `"filnam.ext" ->` | Include Joy source file |
| `abort` | `->` | Abort execution |
| `quit` | `->` | Quit interpreter |

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
- [ ] Tree combinators
- [ ] Time operations (`localtime`, `gmtime`, `strftime`)

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
