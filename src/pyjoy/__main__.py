"""
pyjoy.__main__ - CLI entry point for Joy interpreter.

Usage:
    python -m pyjoy              # Start REPL
    python -m pyjoy -e "1 2 +"   # Execute expression
    python -m pyjoy file.joy     # Execute file
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pyjoy.errors import JoyError
from pyjoy.evaluator import Evaluator
from pyjoy.repl import run_repl


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="pyjoy",
        description="Joy Programming Language Interpreter",
    )
    parser.add_argument(
        "-e",
        "--eval",
        metavar="EXPR",
        help="Evaluate expression and print result",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Joy source file to execute",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Print version and exit",
    )

    args = parser.parse_args()

    if args.version:
        from pyjoy import __version__

        print(f"pyjoy {__version__}")
        return 0

    if args.eval:
        # Execute expression
        return execute_expression(args.eval)

    if args.file:
        # Execute file
        return execute_file(args.file)

    # Start REPL
    run_repl()
    return 0


def execute_expression(expr: str) -> int:
    """Execute a Joy expression and print the stack."""
    evaluator = Evaluator()
    try:
        evaluator.run(expr)
        # Print final stack
        if not evaluator.stack.is_empty():
            for item in evaluator.stack.items():
                print(repr(item))
        return 0
    except JoyError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


def execute_file(filepath: str) -> int:
    """Execute a Joy source file."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        return 1

    try:
        source = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1

    evaluator = Evaluator()
    try:
        evaluator.run(source)
        return 0
    except JoyError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
