"""
pyjoy.__main__ - CLI entry point for Joy interpreter.

Usage:
    python -m pyjoy                     # Start REPL
    python -m pyjoy -e "1 2 +"          # Execute expression
    python -m pyjoy file.joy            # Execute file
    python -m pyjoy compile file.joy    # Compile to C
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from pyjoy.errors import JoyError
from pyjoy.evaluator import Evaluator
from pyjoy.repl import run_repl


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="pyjoy",
        description="Joy Programming Language Interpreter",
        epilog="Subcommands:\n  compile    Compile Joy program to C (use 'pyjoy compile --help')",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Print version and exit",
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
    return parser


def create_compile_parser() -> argparse.ArgumentParser:
    """Create the compile subcommand parser."""
    parser = argparse.ArgumentParser(
        prog="pyjoy compile",
        description="Compile Joy program to C",
    )
    parser.add_argument(
        "source",
        help="Joy source file to compile",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="DIR",
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "-n",
        "--name",
        metavar="NAME",
        help="Output name (default: source file stem)",
    )
    parser.add_argument(
        "--no-compile",
        action="store_true",
        help="Generate C code only, do not compile to executable",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Compile and run the program",
    )
    return parser


def main() -> int:
    """Main entry point."""
    # Check if first argument is 'compile' subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "compile":
        compile_parser = create_compile_parser()
        args = compile_parser.parse_args(sys.argv[2:])
        return compile_to_c(args)

    # Otherwise, use the main parser
    parser = create_parser()
    args = parser.parse_args()

    if args.version:
        from pyjoy import __version__

        print(f"pyjoy {__version__}")
        return 0

    if args.eval:
        return execute_expression(args.eval)

    if args.file:
        return execute_file(args.file)

    # Start REPL
    run_repl()
    return 0


def compile_to_c(args: argparse.Namespace) -> int:
    """Compile Joy source to C."""
    from pyjoy.backends.c import compile_joy_to_c

    # Check for C compiler
    if not shutil.which("gcc") and not shutil.which("clang"):
        print(
            "Error: No C compiler found. Please install gcc or clang.", file=sys.stderr
        )
        return 1

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: File not found: {args.source}", file=sys.stderr)
        return 1

    try:
        source = source_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1

    # Determine output directory and name
    output_dir = Path(args.output) if args.output else Path.cwd()
    target_name = args.name if args.name else source_path.stem

    try:
        result = compile_joy_to_c(
            source,
            output_dir=output_dir,
            target_name=target_name,
            compile_executable=not args.no_compile,
        )

        print(f"Generated: {result['c_file']}")
        print(f"Generated: {result['makefile']}")

        if not args.no_compile:
            print(f"Compiled:  {result['executable']}")

            if args.run:
                import subprocess

                print()
                print("--- Running program ---")
                proc = subprocess.run([str(result["executable"])])
                return proc.returncode

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


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
