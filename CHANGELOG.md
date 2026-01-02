# Changelog

## [Unreleased]

### Fixed
- `filter`/`split`: Now preserve STRING and SET types (were always returning LIST)
  - `"test" ['t <] filter` now returns `"es"` instead of `['e' 's']`
- `all`/`some`: Empty predicate now returns `false` (was returning `true`)
- Comparison operators (`=`, `!=`, `<`, `>`, `<=`, `>=`, `compare`, `equal`):
  - Sets now compare as bitset integers (e.g., `{1 2} = 6`)
  - Empty strings equal 0/false/empty list/empty set
  - Failed file opens (None) equal 0/false
  - Symbols compare with strings by name
  - Non-empty lists never equal with `=` (use `equal` for structural comparison)
  - `compare` handles strings lexicographically, symbols by name, files by identity
- `.` (period) operator: Now properly prints TOS with newline (was being skipped as terminator)
  - No-op when stack is empty (allows use as statement terminator)
  - Revealed ~45 hidden test failures from bugs in primitives
- `stack`: Now returns items with TOS first (was bottom-first)
- `equal` in C runtime: LIST and QUOTATION can now be compared by content
- `equal` in C runtime: INTEGER and FLOAT can now be compared across types
- `ldexp`: Handles overflow by returning infinity instead of raising error
- `format`: Fixed precision handling for integer format specifiers
- Octal character escapes: Scanner now handles `'\010` etc. correctly
- `primrec`: Rewrote to match Joy semantics (push all members, execute I, then C repeatedly)
- `treerec`/`treegenrec`: Fixed recursion pattern to match Joy reference
- `opcase`: Fixed to match by JoyType instead of executing predicates
- `cleave`: Fixed signature from `X [P1 P2 ...]` to `X [P1] [P2] -> R1 R2`
- `construct`: Fixed to push individual results instead of a list

### Added
- `.` primitive: Print TOS with newline (same as `putln` but no-op if stack empty)
- `CONST` keyword: Parser now handles CONST blocks (same as DEFINE/LIBRA)
- `-name` symbols: Scanner handles symbols starting with `-` (like `-inf`)
- `condlinrec` combinator: Conditional linear recursion
- `pick` primitive: Pick element at index N from stack (0=dup, 1=over)
- `unassign` primitive: Remove word definition
- `undeferror`/`setundeferror`: Control undefined word error behavior
- C test build structure: Each Joy file compiles to `build/<stem>/`

### Changed
- `condlinrec`/`condnestrec`: Rewrote to match Joy reference implementation
  - Last clause is now treated as default (no B condition testing)
  - Both combinators share `condnestrecaux` implementation
  - Proper execution order: R1, recurse, R2, recurse, ...
- Standard library loading: `inilib.joy` loaded first, then `agglib.joy`

### Coverage
- Python interpreter: 154/215 Joy tests passing (71.6%)
- C backend: 190/215 Joy tests passing (88.4%)
- pytest: 420/420 unit tests passing (100%)

### Missing Primitives (7)
- `$` - String format/interpolation operator
- `filetime` - Get file modification time
- `finclude` - Include Joy file at runtime
- `id` - Identity function
- `setecho` - Set echo mode
- `setsize` - Set stack size limit
- `__memoryindex` - Memory index for gc

---

## [Previous]

### Fixed
- `not`: Now returns bitwise complement for SETs (was always returning boolean)
- `and`/`or`: Now perform set intersection/union for SET operands
- `cons`: Now supports adding elements to SETs
- `infra`: Now accepts both LIST and QUOTATION arguments

### Added
- `id`: Identity function (does nothing)
- `choice`: B T F -> X (if B then T else F)
- `xor`: Logical XOR / set symmetric difference
- `at`: A I -> X (get element at index I)
- `drop`: A N -> B (drop first N elements)
- `take`: A N -> B (take first N elements)
- `over`: X Y -> X Y X (copy second item to top)
- `dup2`: X Y -> X Y X Y (duplicate top two items)
- `newline`: Print newline
- `unswons`: A -> R F (rest and first, opposite of uncons)
- `of`: I A -> X (get element at index, reverse arg order of `at`)
- `compare`: A B -> I (compare values, return -1/0/1)
- `equal`: T U -> B (recursive structural equality test)
- `in`: X A -> B (membership test)
- `name`: sym -> "sym" (symbol/type to string)
- `intern`: "sym" -> sym (string to symbol)
- `body`: U -> [P] (get body of user-defined word)
- `maxint`: -> I (push maximum integer value)
- `setsize`: -> I (push set size, 64)
- Application combinators: `app1`, `app11`, `app12`, `app2`, `app3`, `app4`
- Arity combinators: `unary2`, `unary3`, `unary4`
- Control flow: `construct`
- Time operations: `localtime`, `gmtime`, `mktime`, `strftime`
- Formatting: `format`, `formatf`
- Case/switch: `opcase`, `case`
- Predicate: `user`
- Tree combinators: `treestep`, `treerec`, `treegenrec`
- Interpreter control: `abort`, `quit`, `gc`, `setautoput`, `autoput`, `echo`, `conts`, `undefs`
- Help system: `help`, `helpdetail`, `manual`
- Compile-time `include` preprocessing with recursive include and circular dependency handling
- File I/O: `fopen`, `fclose`, `fflush`, `feof`, `ferror`, `fgetch`, `fgets`, `fread`, `fput`, `fputch`, `fputchars`, `fputstring`, `fwrite`, `fseek`, `ftell`, `fremove`, `frename`
- System interaction: `system`, `getenv`, `argc`, `argv`
- Arity combinators: `nullary`, `unary`, `binary`, `ternary`, `cleave`
- Type conditionals: `ifinteger`, `ifchar`, `iflogical`, `ifset`, `ifstring`, `iflist`, `iffloat`, `iffile`
- Type predicates: `leaf`, `file`
- Aggregate combinators: `split`, `enconcat`, `some`, `all`
- Stack variants: `rollupd`, `rolldownd`, `rotated`
- File handles: `stdin`, `stdout`, `stderr` (JOY_FILE type support)
- Math primitives: `acos`, `asin`, `atan`, `atan2`, `cosh`, `sinh`, `tanh`, `log10`, `frexp`, `ldexp`, `modf`
- String conversion: `strtol`, `strtod`
- Time/random: `time`, `clock`, `rand`, `srand`
- Recursive combinators: `linrec`, `genrec`, `primrec`
- Set operations with proper set semantics
- Symbol operations: `name`, `intern`, `body`
- Constants: `maxint`

### Tests
- jp-nestrec.joy runs to completion with all tests passing
