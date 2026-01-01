# Changelog

## [Unreleased]

### Fixed
- `condlinrec`/`condnestrec`: Rewrote to match Joy reference implementation
  - Last clause is now treated as default (no B condition testing)
  - Both combinators share `condnestrecaux` implementation
  - Proper execution order: R1, recurse, R2, recurse, ...
- `not`: Now returns bitwise complement for SETs (was always returning boolean)
- `and`/`or`: Now perform set intersection/union for SET operands
- `cons`: Now supports adding elements to SETs
- `infra`: Now accepts both LIST and QUOTATION arguments

### Added
- `over`: X Y -> X Y X (copy second item to top)
- `dup2`: X Y -> X Y X Y (duplicate top two items)
- `newline`: Print newline (alias for `.`)

### Tests
- jp-nestrec.joy now runs to completion with all tests passing
- All 411 pytest tests pass
