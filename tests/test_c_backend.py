"""
Tests for the C code generation backend.
"""

import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pyjoy.backends.c.builder import CBuilder, compile_joy_to_c
from pyjoy.backends.c.converter import CValue, JoyToCConverter
from pyjoy.backends.c.emitter import CEmitter
from pyjoy.backends.c.preprocessor import IncludePreprocessor, preprocess_includes, IncludeError

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
            compile_joy_to_c(
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
            compile_joy_to_c(
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


class TestIncludePreprocessor:
    """Tests for compile-time include expansion."""

    def test_preprocess_no_includes(self):
        """Preprocess source with no includes."""
        source = "1 2 +"
        result = preprocess_includes(source)

        assert len(result.definitions) == 0
        assert len(result.program.terms) == 3

    def test_preprocess_with_definitions(self):
        """Preprocess source with definitions but no includes."""
        source = "DEFINE square == dup * . 5 square"
        result = preprocess_includes(source)

        assert len(result.definitions) == 1
        assert result.definitions[0].name == "square"

    def test_include_simple_file(self):
        """Include a simple Joy file."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create library file
            lib_file = tmppath / "mylib.joy"
            lib_file.write_text("DEFINE double == 2 * .")

            # Create main file
            main_file = tmppath / "main.joy"
            main_source = 'include "mylib.joy"\n5 double'

            result = preprocess_includes(main_source, source_path=main_file)

            # Should have the definition from the included file
            assert len(result.definitions) == 1
            assert result.definitions[0].name == "double"

            # Include should be removed from program
            assert len(result.program.terms) == 2  # 5 and double

    def test_include_with_local_definitions(self):
        """Include file combined with local definitions."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create library file
            lib_file = tmppath / "lib.joy"
            lib_file.write_text("DEFINE inc == 1 + .")

            # Main has both include and local definition
            main_file = tmppath / "main.joy"
            main_source = '''include "lib.joy"
DEFINE double == 2 * .
5 inc double'''

            result = preprocess_includes(main_source, source_path=main_file)

            # Should have both definitions
            assert len(result.definitions) == 2
            names = [d.name for d in result.definitions]
            assert "inc" in names
            assert "double" in names

    def test_recursive_includes(self):
        """Handle recursive includes."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create base library
            base_lib = tmppath / "base.joy"
            base_lib.write_text("DEFINE inc == 1 + .")

            # Create mid library that includes base
            mid_lib = tmppath / "mid.joy"
            mid_lib.write_text('include "base.joy"\nDEFINE double == 2 * .')

            # Main includes mid
            main_file = tmppath / "main.joy"
            main_source = 'include "mid.joy"\n5 inc double'

            result = preprocess_includes(main_source, source_path=main_file)

            # Should have both definitions from recursive includes
            assert len(result.definitions) == 2
            names = [d.name for d in result.definitions]
            assert "inc" in names
            assert "double" in names

    def test_circular_include_handled(self):
        """Circular includes are handled (second include skipped)."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create two files that include each other
            file_a = tmppath / "a.joy"
            file_b = tmppath / "b.joy"

            file_a.write_text('include "b.joy"\nDEFINE from_a == 1 .')
            file_b.write_text('include "a.joy"\nDEFINE from_b == 2 .')

            main_file = tmppath / "main.joy"
            main_source = 'include "a.joy"\n42'

            # Should not infinite loop - circular include is silently skipped
            result = preprocess_includes(main_source, source_path=main_file)

            # Should have definitions from both files
            names = [d.name for d in result.definitions]
            assert "from_a" in names
            assert "from_b" in names

    def test_include_file_not_found(self):
        """Include of non-existent file raises error."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            main_file = tmppath / "main.joy"
            main_source = 'include "nonexistent.joy"\n42'

            with pytest.raises(IncludeError) as exc_info:
                preprocess_includes(main_source, source_path=main_file)

            assert "not found" in str(exc_info.value).lower()

    def test_include_in_quotation_ignored(self):
        """Include inside quotation is not expanded (kept as symbol)."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create library file
            lib_file = tmppath / "lib.joy"
            lib_file.write_text("DEFINE test == 1 .")

            main_file = tmppath / "main.joy"
            # Include in quotation should be kept as-is
            main_source = '[include "lib.joy"] 42'

            result = preprocess_includes(main_source, source_path=main_file)

            # The quotation should still contain "include" and the string
            # (not expanded because it's inside a quotation)
            assert len(result.program.terms) == 2

    def test_compile_with_include(self):
        """Full compilation with include."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create library file
            lib_file = tmppath / "mathlib.joy"
            lib_file.write_text("DEFINE square == dup * .")

            # Create main source
            main_file = tmppath / "main.joy"
            main_source = 'include "mathlib.joy"\n7 square'
            main_file.write_text(main_source)

            # Compile with source_path for include resolution
            result = compile_joy_to_c(
                main_source,
                output_dir=tmppath,
                target_name="test_include",
                compile_executable=True,
                source_path=main_file,
            )

            proc = subprocess.run(
                [str(result["executable"])],
                capture_output=True,
                text=True,
            )

            assert proc.returncode == 0
            assert "49" in proc.stdout  # 7 squared
