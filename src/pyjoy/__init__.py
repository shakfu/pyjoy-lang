"""
pyjoy - An accurate Python implementation of the Joy programming language.

Joy is a functional programming language created by Manfred von Thun.
It is a concatenative, stack-based language where programs are built
by composing functions.
"""

from pyjoy.errors import (
    JoyError,
    JoySetMemberError,
    JoyStackUnderflow,
    JoySyntaxError,
    JoyTypeError,
    JoyUndefinedWord,
)
from pyjoy.evaluator import Evaluator, joy_word
from pyjoy.parser import Parser
from pyjoy.scanner import Scanner, Token
from pyjoy.stack import ExecutionContext, JoyStack
from pyjoy.types import JoyQuotation, JoyType, JoyValue

__version__ = "0.1.0"

__all__ = [
    # Types
    "JoyType",
    "JoyValue",
    "JoyQuotation",
    # Stack
    "JoyStack",
    "ExecutionContext",
    # Scanner
    "Scanner",
    "Token",
    # Parser
    "Parser",
    # Evaluator
    "Evaluator",
    "joy_word",
    # Errors
    "JoyError",
    "JoyStackUnderflow",
    "JoyTypeError",
    "JoyUndefinedWord",
    "JoySyntaxError",
    "JoySetMemberError",
]
