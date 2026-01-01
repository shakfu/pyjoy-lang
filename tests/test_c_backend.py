"""
Tests for the C code generation backend.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from pyjoy.parser import Parser
from pyjoy.backends.c.converter import JoyToCConverter, CProgram, CValue, CQuotation
from pyjoy.backends.c.emitter import CEmitter
from pyjoy.backends.c.builder import CBuilder, compile_joy_to_c


# Skip all tests if no C compiler is available
pytestmark = pytest.mark.skipif(
    not shutil.which("gcc") and not shutil.which("clang"),
    reason="No C compiler available",
)


class TestJoyToCConverter:
    """Tests for Joy-to-C conversion."""

    def test_convert_integer(self):
        """Convert integer literal."""
        source = "42"
        converter = JoyToCConverter()
        program = converter.convert_source(source)

        assert program.main_body is not None
        assert len(program.main_body.terms) == 1
        assert program.main_body.terms[0].type == "integer"
        assert program.main_body.terms[0].value == 42

    def test_convert_float(self):
        """Convert float literal."""
        source = "3.14"
        converter = JoyToCConverter()
        program = converter.convert_source(source)

        assert program.main_body is not None
        assert len(program.main_body.terms) == 1
        assert program.main_body.terms[0].type == "float"
        assert program.main_body.terms[0].value == 3.14

    def test_convert_string(self):
        """Convert string literal."""
        source = '"hello"'
        converter = JoyToCConverter()
        program = converter.convert_source(source)

        assert program.main_body is not None
        assert len(program.main_body.terms) == 1
        assert program.main_body.terms[0].type == "string"
        assert program.main_body.terms[0].value == "hello"

    def test_convert_boolean(self):
        """Convert boolean literals."""
        source = "true false"
        converter = JoyToCConverter()
        program = converter.convert_source(source)

        assert program.main_body is not None
        assert len(program.main_body.terms) == 2
        assert program.main_body.terms[0].type == "boolean"
        assert program.main_body.terms[0].value is True
        assert program.main_body.terms[1].type == "boolean"
        assert program.main_body.terms[1].value is False

    def test_convert_symbol(self):
        """Convert symbol (word reference)."""
        source = "dup swap"
        converter = JoyToCConverter()
        program = converter.convert_source(source)

        assert program.main_body is not None
        assert len(program.main_body.terms) == 2
        assert program.main_body.terms[0].type == "symbol"
        assert program.main_body.terms[0].value == "dup"
        assert program.main_body.terms[1].type == "symbol"
        assert program.main_body.terms[1].value == "swap"

    def test_convert_quotation(self):
        """Convert quotation."""
        source = "[1 2 +]"
        converter = JoyToCConverter()
        program = converter.convert_source(source)

        assert program.main_body is not None
        assert len(program.main_body.terms) == 1
        assert program.main_body.terms[0].type == "quotation"

    def test_convert_definition(self):
        """Convert user-defined word."""
        source = "DEFINE square == dup * . 5 square"
        converter = JoyToCConverter()
        program = converter.convert_source(source)

        assert len(program.definitions) == 1
        assert program.definitions[0].name == "square"
        assert program.main_body is not None

    def test_sanitize_name(self):
        """Sanitize Joy word names for C."""
        converter = JoyToCConverter()

        assert converter._sanitize_name("square") == "square"
        assert converter._sanitize_name("my-word") == "my_word"
        assert converter._sanitize_name("+") == "_plus"
        assert converter._sanitize_name("*") == "_star"
        assert converter._sanitize_name(">=") == "_gt_eq"
        assert converter._sanitize_name("123") == "_123"


class TestCEmitter:
    """Tests for C code emission."""

    def test_emit_header(self):
        """Emit includes header."""
        emitter = CEmitter()
        header = emitter._emit_header()

        assert "#include <stdio.h>" in header
        assert "#include <stdlib.h>" in header
        assert '#include "joy_runtime.h"' in header

    def test_emit_integer_value(self):
        """Emit integer value initializer."""
        emitter = CEmitter()
        value = CValue(type="integer", value=42)

        init = emitter._emit_value_init(value)
        assert init == "joy_integer(42)"

    def test_emit_string_value(self):
        """Emit string value initializer."""
        emitter = CEmitter()
        value = CValue(type="string", value="hello")

        init = emitter._emit_value_init(value)
        assert init == 'joy_string("hello")'

    def test_emit_string_escape(self):
        """Emit escaped string value."""
        emitter = CEmitter()
        value = CValue(type="string", value='hello\n"world"')

        init = emitter._emit_value_init(value)
        assert init == 'joy_string("hello\\n\\"world\\"")'

    def test_emit_simple_program(self):
        """Emit a simple program."""
        source = "42"
        converter = JoyToCConverter()
        program = converter.convert_source(source)

        emitter = CEmitter()
        code = emitter.emit(program)

        assert "joy_integer(42)" in code
        assert "int main(" in code
        assert "joy_context_new()" in code
        assert "joy_runtime_init(ctx)" in code


class TestCBuilder:
    """Tests for C compilation."""

    def test_find_compiler(self):
        """Find an available compiler."""
        builder = CBuilder()
        assert builder.compiler in ["gcc", "clang", "cc"]

    def test_get_runtime_sources(self):
        """Get runtime source files."""
        builder = CBuilder()
        sources = builder.get_runtime_sources()

        assert len(sources) >= 2  # joy_runtime.c and joy_primitives.c
        assert any("joy_runtime.c" in str(s) for s in sources)

    def test_get_runtime_headers(self):
        """Get runtime header files."""
        builder = CBuilder()
        headers = builder.get_runtime_headers()

        assert len(headers) >= 1
        assert any("joy_runtime.h" in str(h) for h in headers)

    def test_generate_makefile(self):
        """Generate Makefile."""
        builder = CBuilder()
        makefile = builder.generate_makefile("program.c", "myprogram")

        assert "TARGET = myprogram" in makefile
        assert "SRCS = program.c" in makefile
        assert "-Wall" in makefile


class TestCompilation:
    """Tests for full compilation and execution."""

    def test_compile_simple_integer(self):
        """Compile and run simple integer program."""
        source = "42"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_program",
                compile_executable=True,
            )

            assert result["c_file"].exists()
            assert result["executable"].exists()

            # Run the executable
            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            # Stack should contain 42
            assert "42" in proc.stdout

    def test_compile_arithmetic(self):
        """Compile and run arithmetic program."""
        source = "3 4 +"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_arith",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert "7" in proc.stdout

    def test_compile_dup_mul(self):
        """Compile dup and multiply program."""
        source = "5 dup *"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_dup",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert "25" in proc.stdout

    def test_compile_quotation(self):
        """Compile program with quotation."""
        source = "5 [dup *] i"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_quot",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert "25" in proc.stdout

    def test_compile_ifte(self):
        """Compile ifte conditional."""
        source = "5 [0 >] [dup *] [0] ifte"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_ifte",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert "25" in proc.stdout

    def test_compile_times(self):
        """Compile times loop."""
        source = "1 5 [2 *] times"  # 1 * 2^5 = 32

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_times",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert "32" in proc.stdout

    def test_compile_definition(self):
        """Compile user definition."""
        source = "DEFINE square == dup * . 7 square"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_def",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert "49" in proc.stdout

    def test_compile_string(self):
        """Compile string literal."""
        source = '"hello" size'

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_str",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert "5" in proc.stdout  # length of "hello"

    def test_compile_list_operations(self):
        """Compile list operations."""
        source = "[1 2 3] first"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_list",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert "1" in proc.stdout

    def test_compile_dip(self):
        """Compile dip combinator."""
        source = "1 2 [10 +] dip +"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_dip",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            # 1 2 [10 +] dip -> 11 2 -> 11 + 2 = 13
            assert "13" in proc.stdout

    def test_compile_map(self):
        """Compile map combinator."""
        source = "[1 2 3] [dup *] map"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_map",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            # [1 4 9]
            assert "1" in proc.stdout
            assert "4" in proc.stdout
            assert "9" in proc.stdout

    def test_compile_fold(self):
        """Compile fold combinator."""
        source = "[1 2 3 4 5] 0 [+] fold"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_fold",
                compile_executable=True,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert "15" in proc.stdout  # 1+2+3+4+5 = 15

    def test_runtime_files_copied(self):
        """Runtime files are copied to output directory."""
        source = "42"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_runtime",
                compile_executable=True,
            )

            output = Path(tmpdir)
            assert (output / "joy_runtime.h").exists()
            assert (output / "joy_runtime.c").exists()
            assert (output / "joy_primitives.c").exists()
            assert (output / "Makefile").exists()

    def test_makefile_works(self):
        """Generated Makefile compiles the program."""
        source = "42"

        with TemporaryDirectory() as tmpdir:
            result = compile_joy_to_c(
                source,
                output_dir=tmpdir,
                target_name="test_make",
                compile_executable=False,  # Don't compile directly
            )

            # Use make to compile
            proc = subprocess.run(
                ["make", "-C", tmpdir],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert (Path(tmpdir) / "test_make").exists()
