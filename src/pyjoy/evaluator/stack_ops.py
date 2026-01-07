"""
pyjoy.evaluator.stack_ops - Stack manipulation primitives.

Contains: dup, pop, swap, stack, unstack, over, rotate, rollup, rolldown,
dupd, popd, swapd, choice, rollupd, rolldownd, dup2
"""

from __future__ import annotations

from pyjoy.errors import JoyTypeError
from pyjoy.stack import ExecutionContext
from pyjoy.types import JoyType, JoyValue

from .core import joy_word


@joy_word(name="dup", params=1, doc="X -> X X")
def dup(ctx: ExecutionContext) -> None:
    """Duplicate top of stack."""
    top = ctx.stack.peek()
    ctx.stack.push_value(top)


@joy_word(name="dup2", params=2, doc="X Y -> X Y X Y")
def dup2(ctx: ExecutionContext) -> None:
    """Duplicate top two items."""
    y = ctx.stack.peek(0)
    x = ctx.stack.peek(1)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)


@joy_word(name="pop", params=1, doc="X ->")
def pop(ctx: ExecutionContext) -> None:
    """Remove top of stack."""
    ctx.stack.pop()


@joy_word(name="id", params=0, doc="->")
def id_(ctx: ExecutionContext) -> None:
    """Identity function (no-op)."""
    pass


@joy_word(name="swap", params=2, doc="X Y -> Y X")
def swap(ctx: ExecutionContext) -> None:
    """Exchange top two stack items."""
    b, a = ctx.stack.pop_n(2)
    ctx.stack.push_value(b)
    ctx.stack.push_value(a)


@joy_word(name="stack", params=0, doc=".. -> .. [..]")
def stack_word(ctx: ExecutionContext) -> None:
    """Push a list of the current stack contents (TOS first)."""
    items = tuple(reversed(ctx.stack.items()))
    ctx.stack.push_value(JoyValue.list(items))


@joy_word(name="unstack", params=1, doc="[X Y ..] -> X Y ..")
def unstack(ctx: ExecutionContext) -> None:
    """Replace stack with contents of list/quotation on top.

    The list is in TOS-first order (same as stack output), so we push
    in reverse order to reconstruct the original stack.
    """
    lst = ctx.stack.pop()
    if lst.type == JoyType.LIST:
        items = lst.value
    elif lst.type == JoyType.QUOTATION:
        # Quotation terms can be executed as a list
        items = lst.value.terms
    else:
        raise JoyTypeError("unstack", "LIST or QUOTATION", lst.type.name)
    ctx.stack.clear()
    # Push in reverse order so first element becomes TOS
    for item in reversed(items):
        if isinstance(item, JoyValue):
            ctx.stack.push_value(item)
        else:
            # Symbol or other term - push as-is
            ctx.stack.push(item)


@joy_word(name="over", params=2, doc="X Y -> X Y X")
def over(ctx: ExecutionContext) -> None:
    """Copy second item to top."""
    second = ctx.stack.peek(1)
    ctx.stack.push_value(second)


@joy_word(name="rotate", params=3, doc="X Y Z -> Z Y X")
def rotate(ctx: ExecutionContext) -> None:
    """Rotate top three items: X Y Z -> Z Y X (flip first and third)."""
    z, y, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(z)
    ctx.stack.push_value(y)
    ctx.stack.push_value(x)


@joy_word(name="rotated", params=4, doc="X Y Z W -> Z Y X W")
def rotated(ctx: ExecutionContext) -> None:
    """Rotate under top: X Y Z W -> Z Y X W."""
    w, z, y, x = ctx.stack.pop_n(4)
    ctx.stack.push_value(z)
    ctx.stack.push_value(y)
    ctx.stack.push_value(x)
    ctx.stack.push_value(w)


@joy_word(name="rollup", params=3, doc="X Y Z -> Z X Y")
def rollup(ctx: ExecutionContext) -> None:
    """Roll up top three items: X Y Z -> Z X Y."""
    z, y, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(z)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)


@joy_word(name="rolldown", params=3, doc="X Y Z -> Y Z X")
def rolldown(ctx: ExecutionContext) -> None:
    """Roll down top three items (same as rotate)."""
    z, y, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(y)
    ctx.stack.push_value(z)
    ctx.stack.push_value(x)


@joy_word(name="rollupd", params=4, doc="X Y Z W -> Z X Y W")
def rollupd(ctx: ExecutionContext) -> None:
    """Rollup under top element: X Y Z W -> Z X Y W."""
    w, z, y, x = ctx.stack.pop_n(4)
    ctx.stack.push_value(z)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)
    ctx.stack.push_value(w)


@joy_word(name="rolldownd", params=4, doc="X Y Z W -> Y Z X W")
def rolldownd(ctx: ExecutionContext) -> None:
    """Rolldown under top element: X Y Z W -> Y Z X W."""
    w, z, y, x = ctx.stack.pop_n(4)
    ctx.stack.push_value(y)
    ctx.stack.push_value(z)
    ctx.stack.push_value(x)
    ctx.stack.push_value(w)


@joy_word(name="dupd", params=2, doc="X Y -> X X Y")
def dupd(ctx: ExecutionContext) -> None:
    """Duplicate second item."""
    y, x = ctx.stack.pop_n(2)
    ctx.stack.push_value(x)
    ctx.stack.push_value(x)
    ctx.stack.push_value(y)


@joy_word(name="popd", params=2, doc="X Y -> Y")
def popd(ctx: ExecutionContext) -> None:
    """Pop second item."""
    y, _ = ctx.stack.pop_n(2)
    ctx.stack.push_value(y)


@joy_word(name="swapd", params=3, doc="X Y Z -> Y X Z")
def swapd(ctx: ExecutionContext) -> None:
    """Swap second and third items."""
    z, y, x = ctx.stack.pop_n(3)
    ctx.stack.push_value(y)
    ctx.stack.push_value(x)
    ctx.stack.push_value(z)


@joy_word(name="choice", params=3, doc="B T F -> X")
def choice(ctx: ExecutionContext) -> None:
    """If B is true, push T, else push F."""
    f, t, b = ctx.stack.pop_n(3)
    if b.is_truthy():
        ctx.stack.push_value(t)
    else:
        ctx.stack.push_value(f)
