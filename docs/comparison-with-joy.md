# PyJoy vs Joy Comparison

This document compares PyJoy with the original Joy programming language, highlighting similarities, differences, and extensions.

## Overview

| Aspect | Joy (C) | PyJoy |
|--------|---------|-------|
| Creator | Manfred von Thun | - |
| Implementation | C | Python 3.13+ |
| Type System | Dynamic, Joy types | Dynamic, dual-mode |
| Interop | Limited | Full Python integration |
| REPL | Basic | Hybrid Joy/Python |
| C Backend | Native | Code generator |

## Syntax Comparison

### Identical Syntax

Most core Joy syntax is preserved in PyJoy:

```joy
(* Comments *)        # Both support Joy-style comments
# Line comments       # PyJoy also supports Python-style

5 dup *               # Stack operations
[1 2 3] first         # List operations
[dup *] map           # Combinators

DEFINE square == dup *.    # Word definitions
```

### Literals

| Type | Joy | PyJoy |
|------|-----|-------|
| Integers | `42`, `-7` | `42`, `-7` |
| Floats | `3.14` | `3.14`, `1e-5` |
| Strings | `"hello"` | `"hello"` (with escapes) |
| Booleans | `true`, `false` | `true`, `false` |
| Characters | `'a` | `'a` or `'a'` |
| Lists | `[1 2 3]` | `[1 2 3]` |
| Sets | `{1 2 3}` | `{1 2 3}` |
| Quotations | `[dup *]` | `[dup *]` |

### Word Definitions

```joy
# Joy style (both)
DEFINE factorial == [0 =] [pop 1] [dup 1 -] [*] linrec.

# Alternative keywords
LIBRA square == dup *.     # Same as DEFINE

# Module syntax
MODULE mymodule
  PRIVATE helper == dup swap.
  PUBLIC main == helper dup.
END.
```

## Word Comparison

### Stack Operations

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `dup` | X -> X X | Same | |
| `pop` | X -> | Same | |
| `swap` | X Y -> Y X | Same | |
| `over` | X Y -> X Y X | Same | |
| `rot` | X Y Z -> Y Z X | Same | |
| `rollup` | X Y Z -> Z X Y | Same | |
| `rolldown` | X Y Z -> Y Z X | Same | |
| `dup2` | X Y -> X Y X Y | Same | |
| `pop2` | X Y -> | Same | |
| `dupd` | X Y -> X X Y | Same | |
| `swapd` | X Y Z -> Y X Z | Same | |
| `popd` | X Y -> Y | Same | |
| `nip` | X Y -> Y | `popd` | Alias |
| `tuck` | X Y -> Y X Y | Same | |
| `depth` | -> N | Same | Stack depth |
| `clear` | ... -> | Same | |
| `stack` | ... -> ... [...] | Same | Copy stack to list |
| `unstack` | [...] -> ... | Same | Replace stack |
| `newstack` | ... -> | Same | Alias for `clear` |

### Arithmetic

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `+`, `-`, `*` | Same | Same | |
| `/` | Integer or float | Same | Result type depends on operands |
| `div` | X Y -> Q R | Same | Quotient and remainder |
| `rem` | X Y -> R | Same | Remainder |
| `neg`, `abs` | Same | Same | |
| `succ`, `pred` | Same | Same | +1, -1 |
| `max`, `min` | Same | Same | |
| `pow` | X Y -> X^Y | Same | |
| `sign` | Same | Same | -1, 0, or 1 |
| `ceil`, `floor` | Same | Same | |
| `trunc`, `round` | Same | Same | |

### Math Functions

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `sin`, `cos`, `tan` | Same | Same | Radians |
| `asin`, `acos`, `atan` | Same | Same | |
| `atan2` | Same | Same | |
| `sinh`, `cosh`, `tanh` | Same | Same | |
| `exp`, `log`, `log10` | Same | Same | |
| `sqrt` | Same | Same | |
| `frexp`, `ldexp`, `modf` | Same | Same | |

### Comparison

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `<`, `<=`, `>`, `>=` | Same | Same | |
| `=` | Equality | Same | Not assignment |
| `!=` | Inequality | Same | |
| `compare` | X Y -> -1/0/1 | Same | Three-way compare |
| `equal` | Deep equality | Same | |

### Logic

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `true`, `false` | Same | Same | Literals |
| `not` | Same | Same | |
| `and`, `or` | Same | Same | |
| `xor` | Same | Same | |

### List/Aggregate Operations

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `first` | Same | Same | |
| `rest` | Same | Same | |
| `cons` | Same | Same | |
| `uncons` | Same | Same | |
| `swons` | Same | Same | `swap cons` |
| `unswons` | Same | Same | |
| `concat` | Same | Same | |
| `size` | Same | Same | |
| `null` | Same | Same | Is empty? |
| `reverse` | Same | Same | |
| `at` | Same | Same | Index access |
| `of` | Same | Same | `swap at` |
| `take`, `drop` | Same | Same | |
| `split` | Same | Same | |
| `small` | Same | Same | 0 or 1 elements |
| `sum`, `product` | Same | Same | |
| `enconcat` | Same | Same | X [A] [B] -> [A X B...] |
| `shunt` | Same | Same | |
| `zip` | Same | Same | |

### String Operations

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `strtol`, `strtof` | Same | Same | Parse numbers |
| `format`, `formatf` | Same | Same | Number to string |
| `chr`, `ord` | Same | Same | Character conversion |

### Combinators

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `i` | Same | Same | Execute quotation |
| `x` | Same | Same | `dup i` |
| `dip` | Same | Same | Execute under top |
| `dipd`, `dipdd` | Same | Same | |
| `app1`, `app2`, `app3`, `app4` | Same | Same | Apply and save |
| `nullary`, `unary`, `binary`, `ternary` | Same | Same | |
| `unary2`, `unary3`, `unary4` | Same | Same | |
| `ifte` | Same | Same | If-then-else |
| `cond` | Same | Same | Multi-way conditional |
| `branch` | Same | Same | Boolean dispatch |
| `iflist`, `ifinteger`, etc. | Same | Same | Type conditionals |
| `loop` | Same | Same | While top is true |
| `while` | Same | Same | Condition + body |
| `times` | Same | Same | N iterations |
| `infra` | Same | Same | Execute on list as stack |
| `map`, `step` | Same | Same | |
| `filter`, `split` | Same | Same | |
| `fold` | Same | Same | |
| `some`, `all` | Same | Same | |
| `cleave` | Same | Same | |
| `construct` | Same | Same | |

### Recursion Combinators

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `linrec` | Same | Same | Linear recursion |
| `binrec` | Same | Same | Binary recursion |
| `genrec` | Same | Same | General recursion |
| `primrec` | Same | Same | Primitive recursion |
| `tailrec` | Same | Same | Tail recursion |
| `condlinrec` | Same | Same | Conditional linear |
| `condnestrec` | Same | Same | Conditional nested |
| `treerec` | Same | Same | Tree recursion |
| `treegenrec` | Same | Same | |
| `treestep` | Same | Same | |

### I/O Operations

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `put` | Same | Same | Print top |
| `putch` | Same | Same | Print character |
| `putchars` | Same | Same | Print string |
| `.` | Same | Same | Print with newline |
| `get` | Same | Same | Read token |
| `getch` | Same | Same | Read character |
| `fopen`, `fclose` | Same | Same | File handle operations |
| `fread`, `fwrite` | Same | Same | |
| `fgets`, `fgetch` | Same | Same | |
| `fput`, `fputch`, `fputchars` | Same | Same | |
| `fseek`, `ftell` | Same | Same | |
| `feof`, `ferror` | Same | Same | |
| `fflush` | Same | Same | |
| `stdin`, `stdout`, `stderr` | Same | Same | Standard streams |

### System Operations

| Operation | Joy | PyJoy | Notes |
|-----------|-----|-------|-------|
| `system` | Same | Same | Execute shell command |
| `getenv` | Same | Same | Environment variable |
| `argc`, `argv` | Same | Same | Command line |
| `time` | Same | Same | Current time |
| `localtime`, `gmtime` | Same | Same | Time conversion |
| `mktime`, `strftime` | Same | Same | |
| `clock` | Same | Same | CPU time |
| `abort`, `quit` | Same | Same | Exit |

## PyJoy Extensions

### Python Integration (Pythonic Mode)

These features are only available when `strict=False`:

```
# Evaluate Python expressions
`math.sqrt(16)`           # Push 4.0
$(len([1,2,3]))           # Push 3

# Execute Python statements
!x = 42
!import numpy as np

# Multi-line Python blocks
def square(x):
    return x * x

# Access stack from Python
`sum(stack)`
`stack[-1]`
```

### REPL Commands

```
.s, .stack   - Show stack with types
.c, .clear   - Clear stack
.w, .words   - List all words
.w PATTERN   - Filter words
.h, .help    - Show help
.help WORD   - Word-specific help
.def N [B]   - Define word (pythonic mode)
.import M    - Import module (pythonic mode)
.load FILE   - Load Joy file
```

### Extended Literals

```
1e-5        # Scientific notation floats
-inf, inf   # Infinity
nan         # Not a number
```

### String Escape Sequences

```
"line1\nline2"    # Newline
"tab\there"       # Tab
"quote\"here"     # Escaped quote
"\x41"            # Hex escape
```

## Known Differences

### Type Coercion

PyJoy is slightly more permissive in some cases:

```joy
# Joy might be stricter about types
# PyJoy in pythonic mode allows duck typing
```

### Set Limitations

Both Joy and PyJoy restrict sets to integers 0-63:

```joy
{0 1 2 63}    # Valid
{64}          # Error: out of range
```

### Character Type

PyJoy supports both Joy-style and quoted character literals:

```joy
'a       # Joy-style (no closing quote)
'a'      # Also valid in PyJoy
'\n'     # Escape sequences work
```

## Migration Tips

1. **Joy programs should work unchanged** in strict mode
2. **Use `.help WORD`** to check word signatures
3. **Set operations** use the same 0-63 restriction
4. **File I/O** works the same way
5. **Recursion combinators** have identical semantics

## Example: Factorial

### Joy Style

```joy
DEFINE factorial == [0 =] [pop 1] [dup 1 -] [*] linrec.
5 factorial.
```

### PyJoy (Same)

```joy
DEFINE factorial == [0 =] [pop 1] [dup 1 -] [*] linrec.
5 factorial .
```

### PyJoy (Pythonic Alternative)

```
> `math.factorial(5)`
Stack: 120
```

## Example: Quicksort

### Joy Style

```joy
DEFINE qsort ==
  [small] []
  [uncons [>] split]
  [enconcat] binrec.
```

### PyJoy (Same)

```joy
DEFINE qsort == [small] [] [uncons [>] split] [enconcat] binrec.
[3 1 4 1 5 9 2 6] qsort .
```

### PyJoy (Using Python)

```
> `sorted([3, 1, 4, 1, 5, 9, 2, 6])`
Stack: [1, 1, 2, 3, 4, 5, 6, 9]
```
