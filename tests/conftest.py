"""
pytest configuration and fixtures for pyjoy tests.
"""

import pytest

from pyjoy.evaluator import Evaluator
from pyjoy.stack import ExecutionContext, JoyStack


@pytest.fixture
def stack():
    """Fresh empty stack."""
    return JoyStack()


@pytest.fixture
def ctx():
    """Fresh execution context."""
    return ExecutionContext()


@pytest.fixture
def evaluator():
    """Fresh evaluator with context."""
    return Evaluator()
