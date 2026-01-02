"""
pyjoy.__main__ - CLI entry point for Joy interpreter.

Usage:
    python -m pyjoy                     # Start REPL
    python -m pyjoy -e "1 2 +"          # Execute expression
    python -m pyjoy file.joy            # Execute file
    python -m pyjoy compile file.joy    # Compile to C
    python -m pyjoy test joy/test2      # Run Joy test suite
"""

from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory

from pyjoy.errors import JoyError
from pyjoy.evaluator import Evaluator
from pyjoy.repl import run_repl


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="pyjoy",
        description="Joy Programming Language Interpreter",
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Print version and exit",
    )
    parser.add_argument(
        "-e", "--eval",
        metavar="EXPR",
        help="Evaluate expression and print result",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run subcommand (for executing files, to avoid conflict with other subcommands)
    run_parser = subparsers.add_parser(
        "run",
        help="Execute a Joy source file",
    )
    run_parser.add_argument(
        "file",
        help="Joy source file to execute",
    )

    # compile subcommand
    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile Joy program to C",
    )
    compile_parser.add_argument(
        "source",
        help="Joy source file to compile",
    )
    compile_parser.add_argument(
        "-o", "--output",
        metavar="DIR",
        help="Output directory (default: current directory)",
    )
    compile_parser.add_argument(
        "-n", "--name",
        metavar="NAME",
        help="Output name (default: source file stem)",
    )
    compile_parser.add_argument(
        "--no-compile",
        action="store_true",
        help="Generate C code only, do not compile to executable",
    )
    compile_parser.add_argument(
        "--run",
        action="store_true",
        help="Compile and run the program",
    )

    # test subcommand
    test_parser = subparsers.add_parser(
        "test",
        help="Run Joy test files",
    )
    test_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory or file to test (default: current directory)",
    )
    test_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show output from each test",
    )
    test_parser.add_argument(
        "-c", "--compile",
        action="store_true",
        help="Also test with C compiler",
    )
    test_parser.add_argument(
        "--pattern",
        default="*.joy",
        help="File pattern to match (default: *.joy)",
    )

    return parser


def main() -> int:
    """Main entry point."""
    # Handle direct file execution (backward compatibility)
    # Check if first arg looks like a file (not a known subcommand)
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if not first_arg.startswith("-") and first_arg not in ("compile", "test", "run"):
            # Likely a file path
            if Path(first_arg).suffix == ".joy" or Path(first_arg).exists():
                return execute_file(first_arg)

    parser = create_parser()
    args = parser.parse_args()

    if args.command == "run":
        return execute_file(args.file)

    if args.command == "compile":
        return cmd_compile(args)

    if args.command == "test":
        return cmd_test(args)

    # No subcommand - handle main parser options
    if args.version:
        from pyjoy import __version__
        print(f"pyjoy {__version__}")
        return 0

    if args.eval:
        return execute_expression(args.eval)

    # Start REPL
    run_repl()
    return 0


def cmd_compile(args: argparse.Namespace) -> int:
    """Compile Joy source to C."""
    from pyjoy.backends.c import compile_joy_to_c

    if not shutil.which("gcc") and not shutil.which("clang"):
        print("Error: No C compiler found. Please install gcc or clang.", file=sys.stderr)
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

    output_dir = Path(args.output) if args.output else Path.cwd()
    target_name = args.name if args.name else source_path.stem

    try:
        result = compile_joy_to_c(
            source,
            output_dir=output_dir,
            target_name=target_name,
            compile_executable=not args.no_compile,
            source_path=source_path,
        )

        print(f"Generated: {result['c_file']}")
        print(f"Generated: {result['makefile']}")

        if not args.no_compile:
            print(f"Compiled:  {result['executable']}")

            if args.run:
                print()
                print("--- Running program ---")
                proc = subprocess.run([str(result["executable"])])
                return proc.returncode

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_test(args: argparse.Namespace) -> int:
    """Run Joy test files."""
    path = Path(args.path)

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob(args.pattern))
    else:
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        return 1

    if not files:
        print(f"No files matching '{args.pattern}' in {args.path}")
        return 1

    passed = 0
    failed = 0
    errors = 0
    failed_tests: list[tuple[str, str]] = []

    print(f"Running {len(files)} Joy tests...", flush=True)
    print(flush=True)

    for filepath in files:
        result, output = run_single_test(filepath, args.verbose)

        if result == "pass":
            passed += 1
            if args.verbose:
                print(f"  PASS: {filepath.name}", flush=True)
        elif result == "fail":
            failed += 1
            failed_tests.append((filepath.name, output))
            print(f"  FAIL: {filepath.name}", flush=True)
            if args.verbose:
                print(f"        Output: {output[:100]}...", flush=True)
        else:  # error
            errors += 1
            failed_tests.append((filepath.name, output))
            print(f"  ERROR: {filepath.name}", flush=True)
            if args.verbose:
                print(f"         {output[:100]}", flush=True)

    # Summary
    print()
    print(f"Results: {passed} passed, {failed} failed, {errors} errors out of {len(files)} tests")

    if failed_tests and not args.verbose:
        print()
        print("Failed tests:")
        for name, output in failed_tests[:10]:
            print(f"  {name}: {output[:80]}")
        if len(failed_tests) > 10:
            print(f"  ... and {len(failed_tests) - 10} more")

    # Run C compilation tests if requested
    if args.compile and (passed > 0 or failed > 0):
        print()
        return cmd_test_compile(files, args.verbose)

    return 0 if (failed == 0 and errors == 0) else 1


def run_single_test(filepath: Path, verbose: bool = False, timeout: float = 5.0) -> tuple[str, str]:
    """Run a single Joy test file.

    Returns: ("pass" | "fail" | "error", output_string)
    """
    import signal

    try:
        source = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return "error", f"Read error: {e}"

    evaluator = Evaluator()
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    def timeout_handler(signum, frame):
        raise TimeoutError("Test timed out")

    try:
        # Set timeout (Unix only)
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                evaluator.run(source)
        finally:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        output = stdout_capture.getvalue()
        errors = stderr_capture.getvalue()

        # Check for "false" in output (indicates test failure)
        if "false" in output.lower():
            return "fail", output.strip()

        # Check for errors
        if errors:
            return "error", errors.strip()

        return "pass", output.strip()

    except TimeoutError:
        return "error", "Test timed out"
    except SystemExit as e:
        # abort/quit calls sys.exit - treat as pass if exit code 0, else error
        if e.code == 0:
            return "pass", "quit called"
        return "error", f"abort/quit with code {e.code}"
    except JoyError as e:
        return "error", f"Joy error: {e}"
    except Exception as e:
        return "error", f"{type(e).__name__}: {e}"


def cmd_test_compile(files: list[Path], verbose: bool = False) -> int:
    """Run C compilation tests on Joy files."""
    from pyjoy.backends.c import compile_joy_to_c

    if not shutil.which("gcc") and not shutil.which("clang"):
        print("Skipping C tests: No compiler available")
        return 0

    print("Running C compilation tests...")
    print()

    passed = 0
    failed = 0

    with TemporaryDirectory() as tmpdir:
        for filepath in files:
            try:
                source = filepath.read_text(encoding="utf-8")
                result = compile_joy_to_c(
                    source,
                    output_dir=tmpdir,
                    target_name=filepath.stem,
                    compile_executable=True,
                    source_path=filepath,
                )

                proc = subprocess.run(
                    [str(result["executable"])],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if "false" in proc.stdout.lower():
                    failed += 1
                    print(f"  FAIL (C): {filepath.name}")
                else:
                    passed += 1
                    if verbose:
                        print(f"  PASS (C): {filepath.name}")

            except Exception as e:
                failed += 1
                print(f"  ERROR (C): {filepath.name} - {e}")

    print()
    print(f"C Results: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def execute_expression(expr: str) -> int:
    """Execute a Joy expression and print the stack."""
    evaluator = Evaluator()
    try:
        evaluator.run(expr)
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
