"""
Tests for Phase 5 I/O and system operations.
"""

import os
import sys
import tempfile

from pyjoy.types import JoyType


class TestOutputPrimitives:
    """Tests for output primitives."""

    def test_put(self, evaluator, capsys):
        """put writes value to stdout."""
        evaluator.run("42 put")
        captured = capsys.readouterr()
        assert "42" in captured.out

    def test_put_string(self, evaluator, capsys):
        """put writes string with quotes."""
        evaluator.run('"hello" put')
        captured = capsys.readouterr()
        assert '"hello"' in captured.out

    def test_putch(self, evaluator, capsys):
        """putch writes single character."""
        evaluator.run("65 putch")  # ASCII 'A'
        captured = capsys.readouterr()
        assert captured.out == "A"

    def test_putchars(self, evaluator, capsys):
        """putchars writes string without quotes."""
        evaluator.run('"hello" putchars')
        captured = capsys.readouterr()
        assert captured.out == "hello"

    def test_newline(self, evaluator, capsys):
        """newline writes a newline."""
        evaluator.run("newline")
        captured = capsys.readouterr()
        assert captured.out == "\n"


class TestStandardStreams:
    """Tests for standard stream primitives."""

    def test_stdin_pushes_file(self, evaluator):
        """stdin pushes a file handle."""
        evaluator.run("stdin")
        result = evaluator.stack.peek()
        assert result.type == JoyType.FILE
        assert result.value is sys.stdin

    def test_stdout_pushes_file(self, evaluator):
        """stdout pushes a file handle."""
        evaluator.run("stdout")
        result = evaluator.stack.peek()
        assert result.type == JoyType.FILE
        assert result.value is sys.stdout

    def test_stderr_pushes_file(self, evaluator):
        """stderr pushes a file handle."""
        evaluator.run("stderr")
        result = evaluator.stack.peek()
        assert result.type == JoyType.FILE
        assert result.value is sys.stderr


class TestFileOperations:
    """Tests for file operations."""

    def test_fopen_fclose(self, evaluator):
        """fopen opens file, fclose closes it."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            fname = f.name

        try:
            evaluator.run(f'"{fname}" "r" fopen')
            result = evaluator.stack.peek()
            assert result.type == JoyType.FILE
            assert result.value is not None

            evaluator.run("fclose")
            assert evaluator.stack.depth == 0
        finally:
            os.unlink(fname)

    def test_fopen_nonexistent(self, evaluator):
        """fopen returns NULL file for nonexistent file."""
        evaluator.run('"/nonexistent/path/file.txt" "r" fopen')
        result = evaluator.stack.peek()
        assert result.type == JoyType.FILE
        assert result.value is None

    def test_fread_fwrite(self, evaluator):
        """fread and fwrite work correctly."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as f:
            fname = f.name

        try:
            # Write bytes
            evaluator.run(f'"{fname}" "wb" fopen')
            evaluator.run("[72 101 108 108 111] fwrite")  # "Hello"
            evaluator.run("fclose")

            # Read bytes back
            evaluator.run(f'"{fname}" "rb" fopen')
            evaluator.run("5 fread")

            # Check the list of bytes
            lst = evaluator.stack.pop()
            assert lst.type == JoyType.LIST
            assert len(lst.value) == 5
            assert lst.value[0].value == 72  # 'H'
            assert lst.value[1].value == 101  # 'e'

            # Clean up
            evaluator.run("fclose")
        finally:
            os.unlink(fname)

    def test_fgets(self, evaluator):
        """fgets reads a line from file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line1\nline2\n")
            fname = f.name

        try:
            evaluator.run(f'"{fname}" "r" fopen')
            evaluator.run("fgets")

            result = evaluator.stack.pop()
            assert result.type == JoyType.STRING
            assert result.value == "line1\n"

            evaluator.run("fclose")
        finally:
            os.unlink(fname)

    def test_ftell_fseek(self, evaluator):
        """ftell and fseek work correctly."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("0123456789")
            fname = f.name

        try:
            evaluator.run(f'"{fname}" "r" fopen')
            evaluator.run("ftell")
            pos = evaluator.stack.pop()
            assert pos.value == 0

            evaluator.run("5 0 fseek")  # Seek to position 5
            evaluator.run("ftell")
            pos = evaluator.stack.pop()
            assert pos.value == 5

            evaluator.run("fclose")
        finally:
            os.unlink(fname)

    def test_fputch_fgetch(self, evaluator):
        """fputch and fgetch work correctly."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as f:
            fname = f.name

        try:
            evaluator.run(f'"{fname}" "w+" fopen')
            evaluator.run("65 fputch")  # Write 'A'
            evaluator.run("0 0 fseek")  # Seek back to start
            evaluator.run("fgetch")

            result = evaluator.stack.pop()
            assert result.type == JoyType.CHAR
            assert result.value == "A"

            evaluator.run("fclose")
        finally:
            os.unlink(fname)


class TestSystemOperations:
    """Tests for system operations."""

    def test_time(self, evaluator):
        """time pushes current epoch time."""
        import time

        before = int(time.time())
        evaluator.run("time")
        after = int(time.time())

        result = evaluator.stack.peek()
        assert result.type == JoyType.INTEGER
        assert before <= result.value <= after + 1

    def test_clock(self, evaluator):
        """clock pushes CPU time in microseconds."""
        evaluator.run("clock")
        result = evaluator.stack.peek()
        assert result.type == JoyType.INTEGER
        assert result.value > 0

    def test_getenv_existing(self, evaluator):
        """getenv gets existing environment variable."""
        os.environ["PYJOY_TEST_VAR"] = "test_value"
        try:
            evaluator.run('"PYJOY_TEST_VAR" getenv')
            result = evaluator.stack.peek()
            assert result.type == JoyType.STRING
            assert result.value == "test_value"
        finally:
            del os.environ["PYJOY_TEST_VAR"]

    def test_getenv_nonexistent(self, evaluator):
        """getenv returns empty string for nonexistent variable."""
        evaluator.run('"NONEXISTENT_VAR_12345" getenv')
        result = evaluator.stack.peek()
        assert result.type == JoyType.STRING
        assert result.value == ""

    def test_argc(self, evaluator):
        """argc pushes argument count."""
        evaluator.run("argc")
        result = evaluator.stack.peek()
        assert result.type == JoyType.INTEGER
        assert result.value >= 0

    def test_argv(self, evaluator):
        """argv pushes argument list."""
        evaluator.run("argv")
        result = evaluator.stack.peek()
        assert result.type == JoyType.LIST


class TestFormatting:
    """Tests for formatting primitives."""

    def test_format_decimal(self, evaluator):
        """format with decimal mode."""
        evaluator.run("42 100 5 0 format")  # 100 = 'd'
        result = evaluator.stack.peek()
        assert result.type == JoyType.STRING
        assert "42" in result.value

    def test_format_hex(self, evaluator):
        """format with hex mode."""
        evaluator.run("255 120 4 0 format")  # 120 = 'x'
        result = evaluator.stack.peek()
        assert result.type == JoyType.STRING
        assert "ff" in result.value.lower()

    def test_format_octal(self, evaluator):
        """format with octal mode."""
        evaluator.run("8 111 4 0 format")  # 111 = 'o'
        result = evaluator.stack.peek()
        assert result.type == JoyType.STRING
        assert "10" in result.value

    def test_formatf(self, evaluator):
        """formatf formats float with format string."""
        evaluator.run('3.14159 "%.2f" formatf')
        result = evaluator.stack.peek()
        assert result.type == JoyType.STRING
        assert result.value == "3.14"


class TestStringConversions:
    """Tests for string conversion primitives."""

    def test_strtol_decimal(self, evaluator):
        """strtol converts string to decimal integer."""
        evaluator.run('"42" 10 strtol')
        result = evaluator.stack.peek()
        assert result.type == JoyType.INTEGER
        assert result.value == 42

    def test_strtol_hex(self, evaluator):
        """strtol converts string to hex integer."""
        evaluator.run('"ff" 16 strtol')
        result = evaluator.stack.peek()
        assert result.type == JoyType.INTEGER
        assert result.value == 255

    def test_strtol_binary(self, evaluator):
        """strtol converts string to binary integer."""
        evaluator.run('"1010" 2 strtol')
        result = evaluator.stack.peek()
        assert result.type == JoyType.INTEGER
        assert result.value == 10

    def test_strtod(self, evaluator):
        """strtod converts string to float."""
        evaluator.run('"3.14" strtod')
        result = evaluator.stack.peek()
        assert result.type == JoyType.FLOAT
        assert abs(result.value - 3.14) < 0.001

    def test_intern(self, evaluator):
        """intern converts string to symbol."""
        evaluator.run('"foo" intern')
        result = evaluator.stack.peek()
        assert result.type == JoyType.SYMBOL
        assert result.value == "foo"

    def test_name(self, evaluator):
        """name converts symbol to string."""
        evaluator.run('"foo" intern name')
        result = evaluator.stack.peek()
        assert result.type == JoyType.STRING
        assert result.value == "foo"


class TestFileRepresentation:
    """Tests for file value representation."""

    def test_file_repr(self, evaluator):
        """File values have proper string representation."""
        evaluator.run("stdin")
        result = evaluator.stack.peek()
        assert "file:" in repr(result)

    def test_null_file_repr(self, evaluator):
        """NULL file has proper representation."""
        evaluator.run('"/nonexistent/path" "r" fopen')
        result = evaluator.stack.peek()
        assert "file:NULL" in repr(result)

    def test_file_truthy(self, evaluator):
        """Open file is truthy, NULL file is falsy."""
        evaluator.run('"/nonexistent/path" "r" fopen null')
        result = evaluator.stack.pop()
        # NULL file should be falsy (null returns true)
        assert result.value is True

        evaluator.run("stdin null")
        result = evaluator.stack.pop()
        # Valid file should be truthy (null returns false)
        assert result.value is False
