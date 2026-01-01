"""
pyjoy.types - Joy type system.

Joy has a strict type system with the following types:
- INTEGER: Arbitrary precision integers
- FLOAT: IEEE 754 double precision floats
- STRING: UTF-8 strings
- CHAR: Single character
- BOOLEAN: true/false
- LIST: Immutable sequences (tuples in Python)
- SET: Sets of integers 0-63 (frozenset in Python)
- QUOTATION: Unevaluated code blocks
- SYMBOL: Word names for definitions
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, FrozenSet, Iterator, Tuple

from pyjoy.errors import JoySetMemberError, JoyTypeError


class JoyType(Enum):
    """Enumeration of Joy value types."""

    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    CHAR = auto()
    BOOLEAN = auto()
    LIST = auto()
    SET = auto()
    QUOTATION = auto()
    SYMBOL = auto()
    FILE = auto()  # File handle for I/O operations


@dataclass(frozen=True, slots=True)
class JoyValue:
    """
    Tagged union for Joy values.

    All Joy values are wrapped in this class with a type tag.
    The value is stored in the `value` attribute.
    """

    type: JoyType
    value: Any

    def __repr__(self) -> str:
        if self.type == JoyType.STRING:
            return f'"{self.value}"'
        elif self.type == JoyType.CHAR:
            return f"'{self.value}'"
        elif self.type == JoyType.BOOLEAN:
            return "true" if self.value else "false"
        elif self.type == JoyType.LIST:
            inner = " ".join(repr(v) for v in self.value)
            return f"[{inner}]"
        elif self.type == JoyType.SET:
            inner = " ".join(str(v) for v in sorted(self.value))
            return "{" + inner + "}"
        elif self.type == JoyType.QUOTATION:
            return repr(self.value)
        elif self.type == JoyType.FILE:
            if self.value is None:
                return "file:NULL"
            return (
                f"file:{self.value.name if hasattr(self.value, 'name') else 'stream'}"
            )
        else:
            return str(self.value)

    # Factory methods for creating JoyValues

    @classmethod
    def integer(cls, n: int) -> JoyValue:
        """Create an INTEGER value."""
        return cls(JoyType.INTEGER, n)

    @classmethod
    def floating(cls, f: float) -> JoyValue:
        """Create a FLOAT value."""
        return cls(JoyType.FLOAT, f)

    @classmethod
    def string(cls, s: str) -> JoyValue:
        """Create a STRING value."""
        return cls(JoyType.STRING, s)

    @classmethod
    def char(cls, c: str) -> JoyValue:
        """Create a CHAR value (single character)."""
        if len(c) != 1:
            raise ValueError(f"CHAR must be single character, got {len(c)} chars")
        return cls(JoyType.CHAR, c)

    @classmethod
    def boolean(cls, b: bool) -> JoyValue:
        """Create a BOOLEAN value."""
        return cls(JoyType.BOOLEAN, b)

    @classmethod
    def list(cls, items: Tuple[JoyValue, ...]) -> JoyValue:
        """Create a LIST value from a tuple of JoyValues."""
        return cls(JoyType.LIST, items)

    @classmethod
    def joy_set(cls, members: FrozenSet[int]) -> JoyValue:
        """Create a SET value. Members must be integers in [0, 63]."""
        for m in members:
            if not (0 <= m <= 63):
                raise JoySetMemberError(m)
        return cls(JoyType.SET, members)

    @classmethod
    def quotation(cls, quot: JoyQuotation) -> JoyValue:
        """Create a QUOTATION value."""
        return cls(JoyType.QUOTATION, quot)

    @classmethod
    def symbol(cls, name: str) -> JoyValue:
        """Create a SYMBOL value."""
        return cls(JoyType.SYMBOL, name)

    @classmethod
    def file(cls, handle: Any) -> JoyValue:
        """Create a FILE value (wraps a Python file object)."""
        return cls(JoyType.FILE, handle)

    # Type checking helpers

    def is_numeric(self) -> bool:
        """Check if value is numeric (INTEGER or FLOAT)."""
        return self.type in (JoyType.INTEGER, JoyType.FLOAT)

    def is_aggregate(self) -> bool:
        """Check if value is an aggregate (LIST, STRING, or SET)."""
        return self.type in (JoyType.LIST, JoyType.STRING, JoyType.SET)

    def is_truthy(self) -> bool:
        """Check if value is truthy in Joy semantics."""
        if self.type == JoyType.BOOLEAN:
            return self.value
        elif self.type == JoyType.INTEGER:
            return self.value != 0
        elif self.type == JoyType.FLOAT:
            return self.value != 0.0
        elif self.type == JoyType.STRING:
            return len(self.value) > 0
        elif self.type == JoyType.LIST:
            return len(self.value) > 0
        elif self.type == JoyType.SET:
            return len(self.value) > 0
        elif self.type == JoyType.QUOTATION:
            return len(self.value.terms) > 0
        elif self.type == JoyType.FILE:
            return self.value is not None
        else:
            return True


class JoyQuotation:
    """
    Represents unevaluated Joy code: [...]

    A quotation is a sequence of terms that can be executed later.
    Terms can be JoyValues, symbols (strings), or nested JoyQuotations.
    """

    __slots__ = ("terms",)

    def __init__(self, terms: Tuple[Any, ...]):
        """Create a quotation from a tuple of terms."""
        self.terms = terms

    def __repr__(self) -> str:
        inner = " ".join(_term_repr(t) for t in self.terms)
        return f"[{inner}]"

    def __iter__(self) -> Iterator[Any]:
        return iter(self.terms)

    def __len__(self) -> int:
        return len(self.terms)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, JoyQuotation):
            return self.terms == other.terms
        return False

    def __hash__(self) -> int:
        return hash(self.terms)


def _term_repr(term: Any) -> str:
    """Get string representation of a term in a quotation."""
    if isinstance(term, JoyValue):
        return repr(term)
    elif isinstance(term, JoyQuotation):
        return repr(term)
    elif isinstance(term, str):
        return term  # Symbol name
    else:
        return repr(term)


def python_to_joy(value: Any) -> JoyValue:
    """
    Convert a Python value to a JoyValue with type inference.

    Args:
        value: Python value to convert

    Returns:
        JoyValue with appropriate type tag

    Raises:
        JoyTypeError: If the value cannot be converted
    """
    if isinstance(value, JoyValue):
        return value

    # Order matters: bool before int (bool is subclass of int in Python)
    if isinstance(value, bool):
        return JoyValue.boolean(value)
    elif isinstance(value, int):
        return JoyValue.integer(value)
    elif isinstance(value, float):
        return JoyValue.floating(value)
    elif isinstance(value, str):
        if len(value) == 1:
            return JoyValue.char(value)
        return JoyValue.string(value)
    elif isinstance(value, tuple):
        # Convert tuple elements recursively
        converted = tuple(python_to_joy(x) for x in value)
        return JoyValue.list(converted)
    elif isinstance(value, list):
        # Convert list to tuple, then to Joy list
        converted = tuple(python_to_joy(x) for x in value)
        return JoyValue.list(converted)
    elif isinstance(value, frozenset):
        # Validate set members
        for m in value:
            if not isinstance(m, int):
                raise JoyTypeError(
                    "python_to_joy", "integer set members", type(m).__name__
                )
        return JoyValue.joy_set(value)
    elif isinstance(value, JoyQuotation):
        return JoyValue.quotation(value)
    else:
        raise JoyTypeError("python_to_joy", "convertible type", type(value).__name__)


def joy_to_python(value: JoyValue) -> Any:
    """
    Convert a JoyValue to a native Python value.

    Args:
        value: JoyValue to convert

    Returns:
        Native Python value
    """
    if value.type == JoyType.LIST:
        return tuple(joy_to_python(v) for v in value.value)
    elif value.type == JoyType.QUOTATION:
        return value.value  # Keep as JoyQuotation
    else:
        return value.value


# Singleton values for common cases
TRUE = JoyValue.boolean(True)
FALSE = JoyValue.boolean(False)
EMPTY_LIST = JoyValue.list(())
EMPTY_SET = JoyValue.joy_set(frozenset())
