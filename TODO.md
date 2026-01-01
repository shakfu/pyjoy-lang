# pyjoy C Backend - TODO

## Primitives Coverage

**Current: 86/203 (42%)** + 8 extensions

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

# jp-nestrec.joy Test Status

**Status: PASSING** - All tests in jp-nestrec.joy now run successfully.

## Working Tests

| Test | Combinator | Status | Notes |
|------|------------|--------|-------|
| r-fact | ifte | PASS | Recursive factorial |
| r-mcc91 | ifte | PASS | McCarthy 91 |
| r-ack | cond | PASS | Ackermann |
| r-hamilhyp | ifte | PASS | Hamiltonian hypercube |
| x-fact | x | PASS | Self-application factorial |
| x-mcc91 | x | PASS | Self-application McCarthy 91 |
| x-ack | x | PASS | Self-application Ackermann |
| y-ack | y | PASS | Y-combinator Ackermann |
| x-hamilhyp | x | PASS | Self-application Hamiltonian |
| l-mcc91 | linrec | PASS | Linear recursion McCarthy 91 |
| l-ack | linrec | PASS | Linear recursion Ackermann |
| lr-hamilhyp | linrec | PASS | Linear recursion Hamiltonian |
| toggle | ifte | PASS | Set toggle operation |
| lr-grayseq | linrec | PASS | Gray sequence with linrec |
| cnr-hamilhyp | condnestrec | PASS | Nested recursion Hamiltonian |
| cnr-ack | condnestrec | PASS | Nested recursion Ackermann (125 = ack(3,4)) |
| cnr-grayseq | condnestrec | PASS | Nested recursion Gray sequence |
| cnr-hanoi | condnestrec | PASS | Towers of Hanoi |
| cnr-fact | condnestrec | PASS | Nested recursion factorial |
| cnr-mcc91 | condnestrec | PASS | Nested recursion McCarthy 91 |
| cnr-even | condnestrec | PASS | Even predicate |
| cnr-abs | condnestrec | PASS | Absolute value |

## Known Issue: clr-ack

The `clr-ack` definition in jp-nestrec.joy uses incorrect format for condlinrec:

```joy
clr-ack ==
    [ [ [pop null]  [popd succ] ]
      [ [null]  [pop pred 1]  [] ]
      [ [[dup pred swap] dip pred]  [clr-ack] ] ]  (* WRONG FORMAT *)
    condlinrec.
```

The last clause uses `[[B] [T]]` format but should use `[[R1] [R2]]` (no B condition).
Compare with the correct format from joy/test2/condlinrec.joy:

```joy
ack == [[[dup null] [pop succ]]
        [[over null] [popd pred 1 swap] []]
        [[dup rollup [pred] dip] [swap pred ack]]]  (* CORRECT: [[R1] [R2]] *)
    condlinrec.
```

## Implementation Notes

### condlinrec/condnestrec Semantics (Fixed)

Based on reference implementation in `joy/src/builtin/condlinrec.c`:

1. Both use shared `condnestrecaux` function
2. Last clause is **default** - NO B condition testing
3. Default format: `[[R1] [R2] ...]` or `[[T]]`
4. Execution: first R, then for each subsequent: recurse, execute

### Set Operations (Fixed)

- `not` on SET: bitwise complement (~)
- `and` on SETs: intersection (&)
- `or` on SETs: union (|)
- `cons` on SET: add element to set

## Test Commands

```bash
# Compile and run jp-nestrec.joy
uv run python -m pyjoy compile tests/examples/jp-nestrec.joy -o build -n jp-nestrec && ./build/jp-nestrec

# Run official Joy tests
uv run python -m pyjoy compile joy/test2/condlinrec.joy -o build -n test && ./build/test
```

## Recent Fixes

- `condlinrec`/`condnestrec`: Rewrote to match reference implementation
- `not`/`and`/`or`: Added set operation support
- `cons`: Added set element insertion
- `infra`: Added quotation support
- Added: `over`, `dup2`, `newline`
