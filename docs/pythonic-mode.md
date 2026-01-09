# Pythonic Mode Guide

A practical guide to using PyJoy's pythonic mode for seamless Python integration.

## Overview

PyJoy supports two execution modes:

| Mode | `strict=True` (default) | `strict=False` (pythonic) |
|------|-------------------------|---------------------------|
| **Stack values** | Wrapped `JoyValue` types | Any Python object |
| **Type system** | Joy's 10 types | Python's duck typing |
| **Lists** | Immutable tuples | Any iterable |
| **Quotations** | `JoyQuotation` AST | JoyQuotation or Python callables |
| **Numbers** | int64/double (Joy spec) | Python arbitrary precision |
| **Python interop** | Not available | Full integration |

## Enabling Pythonic Mode

### Python API

```python
from pyjoy import Evaluator

# Pythonic mode
ev = Evaluator(strict=False)

# Strict mode (default)
ev = Evaluator(strict=True)
```

### REPL

```bash
# Start pythonic REPL
uv run pyjoy --pythonic

# Or in Python
from pyjoy.repl import run_repl
run_repl(strict=False)
```

## Python Integration Syntax

### Backtick Expressions

Evaluate Python expressions and push the result to the stack:

```
> `2 + 3`
Stack: 5

> `math.sqrt(16)`
Stack: 4.0

> `[x**2 for x in range(5)]`
Stack: [0, 1, 4, 9, 16]

> `{"name": "Alice", "age": 30}`
Stack: {'name': 'Alice', 'age': 30}
```

### Dollar Expressions

Alternative syntax, useful when the expression contains backticks:

```
> $(len([1, 2, 3]))
Stack: 3

> $(math.pi * 2)
Stack: 6.283185307179586
```

### Bang Statements

Execute Python statements (no value pushed to stack):

```
> !x = 42
> `x * 2`
Stack: 84

> !import pandas as pd
> !df = pd.DataFrame({"a": [1,2,3]})
> `df`
Stack:    a
       0  1
       1  2
       2  3
```

### Multi-line Python Blocks

The REPL supports multi-line Python blocks. Start a block with `def`, `class`, `if`, `for`, `while`, `with`, `try`, or a decorator (`@`):

```
> def fibonacci(n):
...     if n < 2:
...         return n
...     return fibonacci(n-1) + fibonacci(n-2)
...
  OK

> `fibonacci(10)`
Stack: 55
```

## Pre-imported Modules

In pythonic mode, these modules are automatically available:

- `math` - Mathematical functions
- `json` - JSON encoding/decoding
- `os` - Operating system interface
- `sys` - System-specific parameters
- `re` - Regular expressions
- `itertools` - Iterator building blocks
- `functools` - Higher-order functions
- `collections` - Container datatypes

## Namespace Access

The Python namespace includes:

| Name | Description |
|------|-------------|
| `stack` | The current stack (list-like) |
| `S` | Alias for `stack` |
| `ctx` | The `ExecutionContext` |
| `evaluator` | The `Evaluator` instance |

### Stack Access Examples

```
> 1 2 3
Stack: 1 2 3

> `len(stack)`
Stack: 1 2 3 3

> `sum(stack)`
Stack: 1 2 3 3 6

> `stack[-1]`
Stack: 1 2 3 3 6 6

> !stack.push(100)
Stack: 1 2 3 3 6 6 100
```

## REPL Commands

| Command | Description |
|---------|-------------|
| `.s`, `.stack` | Show stack with types |
| `.c`, `.clear` | Clear the stack |
| `.w`, `.words` | List all available words |
| `.w PATTERN` | List words matching pattern |
| `.h`, `.help` | Show help |
| `.help WORD` | Show help for specific word |
| `.def NAME [BODY]` | Define a new word |
| `.import MODULE` | Import a Python module |
| `.load FILE` | Load a Joy file |
| `quit`, `exit` | Exit the REPL |

### Defining Words

**Joy-style with `.def`:**
```
> .def square [dup *]
  Defined: square
> 5 square
Stack: 25
```

**Using Python:**
```
> def cube(x):
...     return x ** 3
...
  OK

> !WORDS["cube"] = lambda s: s.push(s.pop() ** 3)
> 4 cube
Stack: 64
```

## Mixing Joy and Python

The power of pythonic mode is seamlessly mixing Joy's concatenative style with Python's expressiveness:

```
# Generate with Python, process with Joy
> `range(1, 11)` `list` i
Stack: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

> [2 % 0 =] filter
Stack: [2, 4, 6, 8, 10]

> [dup *] map
Stack: [4, 16, 36, 64, 100]

> 0 [+] fold
Stack: 220
```

### Working with Python Objects

**JSON Processing:**
```
> `'{"users": [{"name": "Alice"}, {"name": "Bob"}]}'`
> `json.loads` i
Stack: {'users': [{'name': 'Alice'}, {'name': 'Bob'}]}

> `lambda d: d["users"]` i
Stack: [{'name': 'Alice'}, {'name': 'Bob'}]

> [`lambda u: u["name"]` i] map
Stack: ['Alice', 'Bob']
```

**NumPy Arrays:**
```
> .import numpy as np
  Imported: numpy as np

> `np.array([1, 2, 3])`
Stack: array([1, 2, 3])

> `np.array([10, 20, 30])`
Stack: array([1, 2, 3]) array([10, 20, 30])

> +
Stack: array([11, 22, 33])
```

**Pandas DataFrames:**
```
> .import pandas as pd
  Imported: pandas as pd

> `pd.DataFrame({"a": [1,2,3], "b": [4,5,6]})`
Stack:    a  b
       0  1  4
       1  2  5
       2  3  6

> `lambda df: df["a"] + df["b"]` i
Stack: 0    5
       1    7
       2    9
       dtype: int64
```

## Decorator Reference

### `@joy_word` - Full Stack Control

Use when you need direct stack access, multiple results, or complex control flow:

```python
from pyjoy.evaluator import joy_word, ExecutionContext
from pyjoy.types import JoyValue

@joy_word(name="rot3", params=3, doc="X Y Z -> Y Z X")
def rot3(ctx: ExecutionContext):
    c, b, a = ctx.stack.pop_n(3)
    ctx.stack.push_value(b)
    ctx.stack.push_value(c)
    ctx.stack.push_value(a)
```

### `@python_word` - Simple Auto-pop/push

Use for pure functions with fixed arity and single return value:

```python
from pyjoy.evaluator import python_word

@python_word(name="hypot", doc="X Y -> Z")
def hypot(x, y):
    return (x**2 + y**2) ** 0.5

# Usage: 3 4 hypot -> 5.0
```

The decorator automatically:
- Pops the required number of arguments
- Unwraps `JoyValue` to raw Python values
- Wraps the result back to `JoyValue` in strict mode
- Pushes the result (if not `None`)

## Design Philosophy

Pythonic mode embraces Python's dynamic nature:

> **The stack is just a Python list. Words are just Python functions. Any Python object can live on the stack.**

This means:
- NumPy arrays can be on the stack
- Pandas DataFrames can be manipulated
- Any Python library is immediately usable
- No translation layer between Joy and Python

### When to Use Each Mode

**Use Strict Mode (`strict=True`) when:**
- Porting existing Joy programs
- Teaching Joy language specifically
- Need exact Joy semantics
- Want predictable type behavior

**Use Pythonic Mode (`strict=False`) when:**
- Building data processing pipelines
- Integrating with Python ecosystem (NumPy, Pandas, etc.)
- Prototyping and experimentation
- Want minimal boilerplate

## Example Session

```
PyJoy - Joy Programming Language Interpreter (Pythonic Mode)
Python interop enabled: `expr`, $(expr), !stmt
Type 'quit' to exit, '.help' for commands.

> 3 4 +
Stack: 7

> `[1, 2, 3, 4, 5]`
Stack: 7 [1, 2, 3, 4, 5]

> [dup *] map
Stack: 7 [1, 4, 9, 16, 25]

> .s
Stack (bottom to top):
  0: (int) 7
  1: (list) [1, 4, 9, 16, 25]

> .c
Stack cleared.

> def is_prime(n):
...     if n < 2: return False
...     return all(n % i != 0 for i in range(2, int(n**0.5)+1))
...
  OK

> `[x for x in range(100) if is_prime(x)]`
Stack: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]

> size
Stack: [2, 3, 5, ..., 97] 25

> quit
```
