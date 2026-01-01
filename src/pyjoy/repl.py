"""
pyjoy.repl - Interactive Read-Eval-Print Loop for Joy.
"""

from __future__ import annotations

from pyjoy.errors import JoyError
from pyjoy.evaluator import Evaluator, list_primitives


class REPL:
    """
    Interactive Joy REPL.

    Commands:
        quit, exit  - Exit the REPL
        .s, .stack  - Show stack with types
        .c, .clear  - Clear the stack
        .w, .words  - List available words
        .h, .help   - Show help
    """

    PROMPT = "> "
    BANNER = """\
PyJoy - Joy Programming Language Interpreter
Type 'quit' to exit, '.help' for commands.
"""

    def __init__(self) -> None:
        self.evaluator = Evaluator()
        self.running = True

    def run(self) -> None:
        """Run the interactive REPL."""
        print(self.BANNER)

        while self.running:
            try:
                line = input(self.PROMPT)
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("\nInterrupted. Type 'quit' to exit.")
                continue

            self._process_line(line)

    def _process_line(self, line: str) -> None:
        """Process a single input line."""
        line = line.strip()

        if not line:
            return

        # Handle REPL commands
        if line in ("quit", "exit"):
            self.running = False
            return

        if line in (".s", ".stack"):
            self._show_stack()
            return

        if line in (".c", ".clear"):
            self.evaluator.stack.clear()
            print("Stack cleared.")
            return

        if line in (".w", ".words"):
            self._show_words()
            return

        if line in (".h", ".help"):
            self._show_help()
            return

        # Execute as Joy code
        try:
            self.evaluator.run(line)
            self._show_stack_brief()
        except JoyError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Internal error: {type(e).__name__}: {e}")

    def _show_stack(self) -> None:
        """Show stack with type information."""
        stack = self.evaluator.stack
        if stack.is_empty():
            print("Stack: (empty)")
            return

        print("Stack (bottom to top):")
        for i, item in enumerate(stack.items()):
            print(f"  {i}: {item.type.name}: {item!r}")

    def _show_stack_brief(self) -> None:
        """Show brief stack representation."""
        stack = self.evaluator.stack
        if stack.is_empty():
            print("Stack: (empty)")
        else:
            items = " ".join(repr(v) for v in stack.items())
            print(f"Stack: {items}")

    def _show_words(self) -> None:
        """Show available words."""
        primitives = list_primitives()
        definitions = sorted(self.evaluator.definitions.keys())

        print("Primitives:")
        # Print in columns
        cols = 6
        for i in range(0, len(primitives), cols):
            row = primitives[i : i + cols]
            print("  " + "  ".join(f"{w:12}" for w in row))

        if definitions:
            print("\nUser definitions:")
            for i in range(0, len(definitions), cols):
                row = definitions[i : i + cols]
                print("  " + "  ".join(f"{w:12}" for w in row))

    def _show_help(self) -> None:
        """Show REPL help."""
        print("""\
REPL Commands:
  quit, exit  - Exit the REPL
  .s, .stack  - Show stack with types
  .c, .clear  - Clear the stack
  .w, .words  - List available words
  .h, .help   - Show this help

Joy Basics:
  42          - Push integer
  3.14        - Push float
  "hello"     - Push string
  'x'         - Push character
  true false  - Push booleans
  [1 2 3]     - Push quotation (list)
  {0 1 2}     - Push set

Stack Operations:
  dup         - Duplicate top
  pop         - Remove top
  swap        - Exchange top two
  i           - Execute quotation
  .           - Print and pop top
""")


def run_repl() -> None:
    """Entry point for running the REPL."""
    repl = REPL()
    repl.run()
