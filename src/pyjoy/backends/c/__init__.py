"""
pyjoy.backends.c - C code generation backend for Joy.

Compiles Joy programs to standalone C executables.
"""

from __future__ import annotations

from .converter import JoyToCConverter
from .emitter import CEmitter
from .builder import CBuilder, compile_joy_to_c

__all__ = ["JoyToCConverter", "CEmitter", "CBuilder", "compile_joy_to_c"]
