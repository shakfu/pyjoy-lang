"""
pyjoy.backends.c.preprocessor - Compile-time include expansion.

This module handles the `include` primitive at compile time by:
1. Detecting `include "filename"` patterns in Joy source
2. Loading and parsing included files
3. Merging definitions from included files
4. Handling recursive includes with circular dependency detection
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Set

from ...parser import Definition, ParseResult, Parser
from ...types import JoyQuotation, JoyType, JoyValue
from ...errors import JoySyntaxError


class IncludeError(JoySyntaxError):
    """Error during include processing."""

    def __init__(self, message: str, file_path: Path | None = None):
        self.file_path = file_path
        super().__init__(message, line=0, column=0)


class IncludePreprocessor:
    """
    Preprocessor that expands `include` directives at compile time.

    Handles:
    - Recursive includes
    - Circular dependency detection
    - Relative path resolution
    """

    def __init__(self, base_path: Path | None = None):
        """
        Initialize the preprocessor.

        Args:
            base_path: Base directory for resolving relative includes.
                      Defaults to current working directory.
        """
        self.base_path = base_path or Path.cwd()
        self._include_stack: List[Path] = []  # For error messages
        self._included_files: Set[Path] = set()  # Prevent re-processing

    def process(self, source: str, source_path: Path | None = None) -> ParseResult:
        """
        Process Joy source code, expanding all includes.

        Args:
            source: Joy source code
            source_path: Path to the source file (for resolving relative includes)

        Returns:
            ParseResult with all includes expanded and merged
        """
        # Determine base path for this source
        if source_path:
            resolved_path = source_path.resolve()
            current_base = resolved_path.parent
            self._included_files.add(resolved_path)
            self._include_stack.append(resolved_path)
        else:
            current_base = self.base_path
            self._include_stack.append(Path("<source>"))

        try:
            # Parse the source
            parser = Parser()
            result = parser.parse_full(source)

            # Collect all definitions (from includes first, then local)
            all_definitions: List[Definition] = []

            # Process the program, expanding includes
            new_terms, included_defs = self._process_terms(
                list(result.program.terms), current_base
            )

            # Add definitions from includes
            all_definitions.extend(included_defs)

            # Add local definitions
            all_definitions.extend(result.definitions)

            return ParseResult(
                definitions=all_definitions,
                program=JoyQuotation(tuple(new_terms)),
            )
        finally:
            self._include_stack.pop()

    def _process_terms(
        self, terms: List[Any], base_path: Path
    ) -> tuple[List[Any], List[Definition]]:
        """
        Process a list of terms, expanding includes.

        Args:
            terms: List of Joy terms
            base_path: Base path for resolving relative includes

        Returns:
            Tuple of (processed terms, collected definitions from includes)
        """
        new_terms: List[Any] = []
        collected_defs: List[Definition] = []
        i = 0

        while i < len(terms):
            term = terms[i]

            # Check for include pattern: symbol "include" followed by string
            if self._is_include_symbol(term):
                if i + 1 < len(terms):
                    next_term = terms[i + 1]
                    if self._is_string_value(next_term):
                        # Found include "filename" pattern
                        filename = self._get_string_value(next_term)
                        include_defs = self._process_include(filename, base_path)
                        collected_defs.extend(include_defs)
                        i += 2  # Skip both include and filename
                        continue

            # Process nested quotations
            if isinstance(term, JoyQuotation):
                processed_terms, nested_defs = self._process_terms(
                    list(term.terms), base_path
                )
                collected_defs.extend(nested_defs)
                new_terms.append(JoyQuotation(tuple(processed_terms)))
            elif isinstance(term, JoyValue) and term.type == JoyType.QUOTATION:
                processed_terms, nested_defs = self._process_terms(
                    list(term.value.terms), base_path
                )
                collected_defs.extend(nested_defs)
                new_terms.append(JoyValue.quotation(JoyQuotation(tuple(processed_terms))))
            else:
                new_terms.append(term)

            i += 1

        return new_terms, collected_defs

    def _is_include_symbol(self, term: Any) -> bool:
        """Check if term is the 'include' symbol."""
        if isinstance(term, str):
            return term == "include"
        if isinstance(term, JoyValue) and term.type == JoyType.SYMBOL:
            return term.value == "include"
        return False

    def _is_string_value(self, term: Any) -> bool:
        """Check if term is a string value."""
        return isinstance(term, JoyValue) and term.type == JoyType.STRING

    def _get_string_value(self, term: JoyValue) -> str:
        """Extract string value from JoyValue."""
        return term.value

    def _process_include(
        self, filename: str, base_path: Path
    ) -> List[Definition]:
        """
        Process an include directive.

        Args:
            filename: The filename to include
            base_path: Base path for resolving relative paths

        Returns:
            List of definitions from the included file
        """
        # Resolve the include path
        include_path = (base_path / filename).resolve()

        # Check for circular includes
        if include_path in self._included_files:
            # Already included - skip silently (not an error)
            return []

        # Check if file exists
        if not include_path.exists():
            stack_str = " -> ".join(str(p) for p in self._include_stack)
            raise IncludeError(
                f"Include file not found: {filename}\n"
                f"  Resolved to: {include_path}\n"
                f"  Include stack: {stack_str}",
                include_path,
            )

        # Mark as included
        self._included_files.add(include_path)
        self._include_stack.append(include_path)

        try:
            # Read and parse the included file
            source = include_path.read_text()
            parser = Parser()
            result = parser.parse_full(source)

            # Recursively process includes in the included file
            new_base = include_path.parent
            _, nested_defs = self._process_terms(
                list(result.program.terms), new_base
            )

            # Collect definitions: nested includes first, then this file's defs
            all_defs: List[Definition] = []
            all_defs.extend(nested_defs)
            all_defs.extend(result.definitions)

            return all_defs

        finally:
            self._include_stack.pop()


def preprocess_includes(
    source: str,
    source_path: Path | str | None = None,
    base_path: Path | str | None = None,
) -> ParseResult:
    """
    Preprocess Joy source code, expanding all includes.

    This is the main entry point for include preprocessing.

    Args:
        source: Joy source code
        source_path: Path to the source file (for resolving relative includes)
        base_path: Base directory for resolving includes if source_path not provided

    Returns:
        ParseResult with all includes expanded and definitions merged

    Example:
        >>> result = preprocess_includes(
        ...     'include "stdlib.joy" 5 fact .',
        ...     source_path=Path("myprogram.joy")
        ... )
    """
    if isinstance(source_path, str):
        source_path = Path(source_path)
    if isinstance(base_path, str):
        base_path = Path(base_path)

    preprocessor = IncludePreprocessor(base_path=base_path)
    return preprocessor.process(source, source_path=source_path)
