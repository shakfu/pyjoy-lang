"""
Joy primitives dictionary and utilities.

This module provides:
- PRIMITIVES: Dict of all Joy primitives with signatures and descriptions
- SECTIONS: Primitives organized by category
- is_primitive(): Check if a name is a known primitive
- get_help(): Get help text for a primitive
- check_coverage(): Compare implementation against Joy spec
"""

from typing import Dict, List, Optional, Set, Tuple

# =============================================================================
# Joy Primitives Data (from Joy manual)
# =============================================================================

PRIMITIVES: Dict[str, Dict] = {
    "!=": {
        "description": "Either both X and Y are numeric or both are strings or symbols. "
        "Tests whether X not equal to Y. Also supports float.",
        "name": "!=",
        "section": "predicate",
        "signature": "X Y  ->  B",
    },
    "*": {
        "description": "Integer K is the product of integers I and J. Also supports float.",
        "name": "*",
        "section": "operator",
        "signature": "I J  ->  K",
    },
    "+": {
        "description": "Numeric N is the result of adding integer I to numeric M. Also supports float.",
        "name": "+",
        "section": "operator",
        "signature": "M I  ->  N",
    },
    "-": {
        "description": "Numeric N is the result of subtracting integer I from numeric M. Also supports float.",
        "name": "-",
        "section": "operator",
        "signature": "M I  ->  N",
    },
    "/": {
        "description": "Integer K is the (rounded) ratio of integers I and J. Also supports float.",
        "name": "/",
        "section": "operator",
        "signature": "I J  ->  K",
    },
    "<": {
        "description": "Either both X and Y are numeric or both are strings or symbols. "
        "Tests whether X less than Y. Also supports float.",
        "name": "<",
        "section": "predicate",
        "signature": "X Y  ->  B",
    },
    "<=": {
        "description": "Either both X and Y are numeric or both are strings or symbols. "
        "Tests whether X less than or equal to Y. Also supports float.",
        "name": "<=",
        "section": "predicate",
        "signature": "X Y  ->  B",
    },
    "=": {
        "description": "Either both X and Y are numeric or both are strings or symbols. "
        "Tests whether X equal to Y. Also supports float.",
        "name": "=",
        "section": "predicate",
        "signature": "X Y  ->  B",
    },
    ">": {
        "description": "Either both X and Y are numeric or both are strings or symbols. "
        "Tests whether X greater than Y. Also supports float.",
        "name": ">",
        "section": "predicate",
        "signature": "X Y  ->  B",
    },
    ">=": {
        "description": "Either both X and Y are numeric or both are strings or symbols. "
        "Tests whether X greater than or equal to Y. Also supports float.",
        "name": ">=",
        "section": "predicate",
        "signature": "X Y  ->  B",
    },
    "abort": {
        "description": "Aborts execution of current Joy program, returns to Joy main cycle.",
        "name": "abort",
        "section": "miscellaneous commands",
        "signature": "->",
    },
    "abs": {
        "description": "Integer N2 is the absolute value (0,1,2..) of integer N1, "
        "or float N2 is the absolute value (0.0 ..) of float N1",
        "name": "abs",
        "section": "operator",
        "signature": "N1  ->  N2",
    },
    "acos": {
        "description": "G is the arc cosine of F.",
        "name": "acos",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "all": {
        "description": "Applies test B to members of aggregate A, X = true if all pass.",
        "name": "all",
        "section": "combinator",
        "signature": "A [B]  ->  X",
    },
    "and": {
        "description": "Z is the intersection of sets X and Y, logical conjunction for truth values.",
        "name": "and",
        "section": "operator",
        "signature": "X Y  ->  Z",
    },
    "app1": {
        "description": "Executes P, pushes result R on stack without X.",
        "name": "app1",
        "section": "combinator",
        "signature": "X [P]  ->  R",
    },
    "app11": {
        "description": "Executes P, pushes result R on stack.",
        "name": "app11",
        "section": "combinator",
        "signature": "X Y [P]  ->  R",
    },
    "app12": {
        "description": "Executes P twice, with Y1 and Y2, returns R1 and R2.",
        "name": "app12",
        "section": "combinator",
        "signature": "X Y1 Y2 [P]  ->  R1 R2",
    },
    "app2": {
        "description": "Obsolescent. == unary2",
        "name": "app2",
        "section": "combinator",
        "signature": "X1 X2 [P]  ->  R1 R2",
    },
    "app3": {
        "description": "Obsolescent. == unary3",
        "name": "app3",
        "section": "combinator",
        "signature": "X1 X2 X3 [P]  ->  R1 R2 R3",
    },
    "app4": {
        "description": "Obsolescent. == unary4",
        "name": "app4",
        "section": "combinator",
        "signature": "X1 X2 X3 X4 [P]  ->  R1 R2 R3 R4",
    },
    "argc": {
        "description": "Pushes the number of command line arguments. Equivalent to 'argv size'.",
        "name": "argc",
        "section": "miscellaneous commands",
        "signature": "-> I",
    },
    "argv": {
        "description": "Creates an aggregate A containing the interpreter's command line arguments.",
        "name": "argv",
        "section": "miscellaneous commands",
        "signature": "-> A",
    },
    "asin": {
        "description": "G is the arc sine of F.",
        "name": "asin",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "at": {
        "description": "X (= A[I]) is the member of A at position I.",
        "name": "at",
        "section": "operator",
        "signature": "A I  ->  X",
    },
    "atan": {
        "description": "G is the arc tangent of F.",
        "name": "atan",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "atan2": {
        "description": "H is the arc tangent of F / G.",
        "name": "atan2",
        "section": "operator",
        "signature": "F G  ->  H",
    },
    "autoput": {
        "description": "Pushes current value of flag for automatic output, I = 0..2.",
        "name": "autoput",
        "section": "operand",
        "signature": "->  I",
    },
    "binary": {
        "description": "Executes P, which leaves R on top of the stack. "
        "No matter how many parameters this consumes, exactly two are removed from the stack.",
        "name": "binary",
        "section": "combinator",
        "signature": "X Y [P]  ->  R",
    },
    "binrec": {
        "description": "Executes P. If that yields true, executes T. "
        "Else uses R1 to produce two intermediates, recurses on both, "
        "then executes R2 to combine their results.",
        "name": "binrec",
        "section": "combinator",
        "signature": "[B] [T] [R1] [R2]  ->  ...",
    },
    "body": {
        "description": "Quotation [P] is the body of user-defined symbol U.",
        "name": "body",
        "section": "operator",
        "signature": "U  ->  [P]",
    },
    "branch": {
        "description": "If B is true, then executes T else executes F.",
        "name": "branch",
        "section": "combinator",
        "signature": "B [T] [F]  ->  ...",
    },
    "case": {
        "description": "Indexing on the value of X, execute the matching Y.",
        "name": "case",
        "section": "operator",
        "signature": "X [..[X Y]..]  ->  Y i",
    },
    "ceil": {
        "description": "G is the float ceiling of F.",
        "name": "ceil",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "char": {
        "description": "Tests whether X is a character.",
        "name": "char",
        "section": "predicate",
        "signature": "X  ->  B",
    },
    "choice": {
        "description": "If B is true, then X = T else X = F.",
        "name": "choice",
        "section": "operator",
        "signature": "B T F  ->  X",
    },
    "chr": {
        "description": "C is the character whose Ascii value is integer I (or logical or character).",
        "name": "chr",
        "section": "operator",
        "signature": "I  ->  C",
    },
    "cleave": {
        "description": "Executes P1 and P2, each with X on top, producing two results.",
        "name": "cleave",
        "section": "combinator",
        "signature": "X [P1] [P2]  ->  R1 R2",
    },
    "clock": {
        "description": "Pushes the integer value of current CPU usage in hundreds of a second.",
        "name": "clock",
        "section": "operand",
        "signature": "->  I",
    },
    "compare": {
        "description": "I (=-1,0,+1) is the comparison of aggregates A and B. "
        "The values correspond to the predicates <=, =, >=.",
        "name": "compare",
        "section": "operator",
        "signature": "A B  ->  I",
    },
    "concat": {
        "description": "Sequence U is the concatenation of sequences S and T.",
        "name": "concat",
        "section": "operator",
        "signature": "S T  ->  U",
    },
    "cond": {
        "description": "Tries each Bi. If that yields true, then executes Ti and exits. "
        "If no Bi yields true, executes default D.",
        "name": "cond",
        "section": "combinator",
        "signature": "[..[[Bi] Ti]..[D]]  ->  ...",
    },
    "condlinrec": {
        "description": "Each [Ci] is of the forms [[B] [T]] or [[B] [R1] [R2]]. "
        "Tries each B. If that yields true and there is just a [T], executes T and exit. "
        "If there are [R1] and [R2], executes R1, recurses, executes R2. "
        "If no B yields true, then [D] is used.",
        "name": "condlinrec",
        "section": "combinator",
        "signature": "[ [C1] [C2] .. [D] ]  ->  ...",
    },
    "cons": {
        "description": "Aggregate B is A with a new member X (first member for sequences).",
        "name": "cons",
        "section": "operator",
        "signature": "X A  ->  B",
    },
    "construct": {
        "description": "Saves state of stack and then executes [P]. "
        "Then executes each [Pi] to give Ri pushed onto saved stack.",
        "name": "construct",
        "section": "combinator",
        "signature": "[P] [[P1] [P2] ..]  ->  R1 R2 ..",
    },
    "conts": {
        "description": "Pushes current continuations. Buggy, do not use.",
        "name": "conts",
        "section": "operand",
        "signature": "->  [[P] [Q] ..]",
    },
    "cos": {
        "description": "G is the cosine of F.",
        "name": "cos",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "cosh": {
        "description": "G is the hyperbolic cosine of F.",
        "name": "cosh",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "dip": {
        "description": "Saves X, executes P, pushes X back.",
        "name": "dip",
        "section": "combinator",
        "signature": "X [P]  ->  ... X",
    },
    "div": {
        "description": "Integers K and L are the quotient and remainder of dividing I by J.",
        "name": "div",
        "section": "operator",
        "signature": "I J  ->  K L",
    },
    "drop": {
        "description": "Aggregate B is the result of deleting the first N elements of A.",
        "name": "drop",
        "section": "operator",
        "signature": "A N  ->  B",
    },
    "dup": {
        "description": "Pushes an extra copy of X onto stack.",
        "name": "dup",
        "section": "operator",
        "signature": "X  ->   X X",
    },
    "dupd": {
        "description": "As if defined by: dupd == [dup] dip",
        "name": "dupd",
        "section": "operator",
        "signature": "Y Z  ->  Y Y Z",
    },
    "echo": {
        "description": "Pushes value of echo flag, I = 0..3.",
        "name": "echo",
        "section": "operand",
        "signature": "->  I",
    },
    "enconcat": {
        "description": "Sequence U is the concatenation of sequences S and T "
        "with X inserted between S and T (== swapd cons concat)",
        "name": "enconcat",
        "section": "operator",
        "signature": "X S T  ->  U",
    },
    "equal": {
        "description": "(Recursively) tests whether trees T and U are identical.",
        "name": "equal",
        "section": "predicate",
        "signature": "T U  ->  B",
    },
    "exp": {
        "description": "G is e (2.718281828...) raised to the Fth power.",
        "name": "exp",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "false": {
        "description": "Pushes the value false.",
        "name": "false",
        "section": "operand",
        "signature": "->  false",
    },
    "fclose": {
        "description": "Stream S is closed and removed from the stack.",
        "name": "fclose",
        "section": "operator",
        "signature": "S  ->",
    },
    "feof": {
        "description": "B is the end-of-file status of stream S.",
        "name": "feof",
        "section": "operator",
        "signature": "S  ->  S B",
    },
    "ferror": {
        "description": "B is the error status of stream S.",
        "name": "ferror",
        "section": "operator",
        "signature": "S  ->  S B",
    },
    "fflush": {
        "description": "Flush stream S, forcing all buffered output to be written.",
        "name": "fflush",
        "section": "operator",
        "signature": "S  ->  S",
    },
    "fgetch": {
        "description": "C is the next available character from stream S.",
        "name": "fgetch",
        "section": "operator",
        "signature": "S  ->  S C",
    },
    "fgets": {
        "description": "L is the next available line (as a string) from stream S.",
        "name": "fgets",
        "section": "operator",
        "signature": "S  ->  S L",
    },
    "file": {
        "description": "Tests whether F is a file.",
        "name": "file",
        "section": "predicate",
        "signature": "F  ->  B",
    },
    "filter": {
        "description": "Uses test B to filter aggregate A producing sametype aggregate A1.",
        "name": "filter",
        "section": "combinator",
        "signature": "A [B]  ->  A1",
    },
    "first": {
        "description": "F is the first member of the non-empty aggregate A.",
        "name": "first",
        "section": "operator",
        "signature": "A  ->  F",
    },
    "float": {
        "description": "Tests whether R is a float.",
        "name": "float",
        "section": "predicate",
        "signature": "R  ->  B",
    },
    "floor": {
        "description": "G is the floor of F.",
        "name": "floor",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "fold": {
        "description": "Starting with value V0, sequentially pushes members of aggregate A "
        "and combines with binary operator P to produce value V.",
        "name": "fold",
        "section": "combinator",
        "signature": "A V0 [P]  ->  V",
    },
    "fopen": {
        "description": "The file system object with pathname P is opened with mode M (r, w, a, etc.) "
        "and stream object S is pushed; if the open fails, file:NULL is pushed.",
        "name": "fopen",
        "section": "operator",
        "signature": "P M  ->  S",
    },
    "format": {
        "description": "S is the formatted version of N in mode C "
        "('d or 'i = decimal, 'o = octal, 'x or 'X = hex) "
        "with maximum width I and minimum width J.",
        "name": "format",
        "section": "operator",
        "signature": "N C I J  ->  S",
    },
    "formatf": {
        "description": "S is the formatted version of F in mode C "
        "('e or 'E = exponential, 'f = fractional, 'g or G = general) "
        "with maximum width I and precision J.",
        "name": "formatf",
        "section": "operator",
        "signature": "F C I J  ->  S",
    },
    "fput": {
        "description": "Writes X to stream S, pops X off stack.",
        "name": "fput",
        "section": "operator",
        "signature": "S X  ->  S",
    },
    "fputch": {
        "description": "The character C is written to the current position of stream S.",
        "name": "fputch",
        "section": "operator",
        "signature": "S C  ->  S",
    },
    "fputchars": {
        "description": "The string abc.. (no quotes) is written to the current position of stream S.",
        "name": "fputchars",
        "section": "operator",
        "signature": 'S "abc.."  ->  S',
    },
    "fputstring": {
        "description": "== fputchars, as a temporary alternative.",
        "name": "fputstring",
        "section": "operator",
        "signature": 'S "abc.."  ->  S',
    },
    "fread": {
        "description": "I bytes are read from the current position of stream S "
        "and returned as a list of I integers.",
        "name": "fread",
        "section": "operator",
        "signature": "S I  ->  S L",
    },
    "fremove": {
        "description": "The file system object with pathname P is removed from the file system. "
        "B is a boolean indicating success or failure.",
        "name": "fremove",
        "section": "operator",
        "signature": "P  ->  B",
    },
    "frename": {
        "description": "The file system object with pathname P1 is renamed to P2. "
        "B is a boolean indicating success or failure.",
        "name": "frename",
        "section": "operator",
        "signature": "P1 P2  ->  B",
    },
    "frexp": {
        "description": "G is the mantissa and I is the exponent of F. Unless F = 0, 0.5 <= abs(G) < 1.0.",
        "name": "frexp",
        "section": "operator",
        "signature": "F  ->  G I",
    },
    "fseek": {
        "description": "Stream S is repositioned to position P relative to whence-point W, "
        "where W = 0, 1, 2 for beginning, current position, end respectively.",
        "name": "fseek",
        "section": "operator",
        "signature": "S P W  ->  S",
    },
    "ftell": {
        "description": "I is the current position of stream S.",
        "name": "ftell",
        "section": "operator",
        "signature": "S  ->  S I",
    },
    "fwrite": {
        "description": "A list of integers are written as bytes to the current position of stream S.",
        "name": "fwrite",
        "section": "operator",
        "signature": "S L  ->  S",
    },
    "gc": {
        "description": "Initiates garbage collection.",
        "name": "gc",
        "section": "miscellaneous commands",
        "signature": "->",
    },
    "genrec": {
        "description": "Executes B, if that yields true executes T. "
        "Else executes R1 and then [[B] [T] [R1] [R2] genrec] R2.",
        "name": "genrec",
        "section": "combinator",
        "signature": "[B] [T] [R1] [R2]  ->  ...",
    },
    "get": {
        "description": "Reads a factor from input and pushes it onto stack.",
        "name": "get",
        "section": "miscellaneous commands",
        "signature": "->  F",
    },
    "getenv": {
        "description": 'Retrieves the value of the environment variable "variable".',
        "name": "getenv",
        "section": "miscellaneous commands",
        "signature": '"variable"  ->  "value"',
    },
    "gmtime": {
        "description": "Converts a time I into a list T representing universal time: "
        "[year month day hour minute second isdst yearday weekday].",
        "name": "gmtime",
        "section": "operator",
        "signature": "I  ->  T",
    },
    "has": {
        "description": "Tests whether aggregate A has X as a member.",
        "name": "has",
        "section": "predicate",
        "signature": "A X  ->  B",
    },
    "help": {
        "description": "Lists all defined symbols, including those from library files. "
        "Then lists all primitives of raw Joy.",
        "name": "help",
        "section": "miscellaneous commands",
        "signature": "->",
    },
    "helpdetail": {
        "description": "Gives brief help on each symbol S in the list.",
        "name": "helpdetail",
        "section": "miscellaneous commands",
        "signature": "[ S1  S2  .. ]",
    },
    "i": {
        "description": "Executes P. So, [P] i == P.",
        "name": "i",
        "section": "combinator",
        "signature": "[P]  ->  ...",
    },
    "id": {
        "description": "Identity function, does nothing. Any program of the form P id Q is equivalent to just P Q.",
        "name": "id",
        "section": "operator",
        "signature": "->",
    },
    "ifchar": {
        "description": "If X is a character, executes T else executes E.",
        "name": "ifchar",
        "section": "combinator",
        "signature": "X [T] [E]  ->  ...",
    },
    "iffile": {
        "description": "If X is a file, executes T else executes E.",
        "name": "iffile",
        "section": "combinator",
        "signature": "X [T] [E]  ->  ...",
    },
    "iffloat": {
        "description": "If X is a float, executes T else executes E.",
        "name": "iffloat",
        "section": "combinator",
        "signature": "X [T] [E]  ->  ...",
    },
    "ifinteger": {
        "description": "If X is an integer, executes T else executes E.",
        "name": "ifinteger",
        "section": "combinator",
        "signature": "X [T] [E]  ->  ...",
    },
    "iflist": {
        "description": "If X is a list, executes T else executes E.",
        "name": "iflist",
        "section": "combinator",
        "signature": "X [T] [E]  ->  ...",
    },
    "iflogical": {
        "description": "If X is a logical or truth value, executes T else executes E.",
        "name": "iflogical",
        "section": "combinator",
        "signature": "X [T] [E]  ->  ...",
    },
    "ifset": {
        "description": "If X is a set, executes T else executes E.",
        "name": "ifset",
        "section": "combinator",
        "signature": "X [T] [E]  ->  ...",
    },
    "ifstring": {
        "description": "If X is a string, executes T else executes E.",
        "name": "ifstring",
        "section": "combinator",
        "signature": "X [T] [E]  ->  ...",
    },
    "ifte": {
        "description": "Executes B. If that yields true, then executes T else executes F.",
        "name": "ifte",
        "section": "combinator",
        "signature": "[B] [T] [F]  ->  ...",
    },
    "in": {
        "description": "Tests whether X is a member of aggregate A.",
        "name": "in",
        "section": "predicate",
        "signature": "X A  ->  B",
    },
    "include": {
        "description": 'Transfers input to file whose name is "filnam.ext". '
        "On end-of-file returns to previous input file.",
        "name": "include",
        "section": "miscellaneous commands",
        "signature": '"filnam.ext"  ->',
    },
    "infra": {
        "description": "Using list L1 as stack, executes P and returns a new list L2. "
        "The first element of L1 is used as the top of stack.",
        "name": "infra",
        "section": "combinator",
        "signature": "L1 [P]  ->  L2",
    },
    "integer": {
        "description": "Tests whether X is an integer.",
        "name": "integer",
        "section": "predicate",
        "signature": "X  ->  B",
    },
    "intern": {
        "description": 'Pushes the item whose name is "sym".',
        "name": "intern",
        "section": "operator",
        "signature": '"sym"  -> sym',
    },
    "ldexp": {
        "description": "G is F times 2 to the Ith power.",
        "name": "ldexp",
        "section": "operator",
        "signature": "F I  -> G",
    },
    "leaf": {
        "description": "Tests whether X is not a list.",
        "name": "leaf",
        "section": "predicate",
        "signature": "X  ->  B",
    },
    "linrec": {
        "description": "Executes P. If that yields true, executes T. Else executes R1, recurses, executes R2.",
        "name": "linrec",
        "section": "combinator",
        "signature": "[P] [T] [R1] [R2]  ->  ...",
    },
    "list": {
        "description": "Tests whether X is a list.",
        "name": "list",
        "section": "predicate",
        "signature": "X  ->  B",
    },
    "localtime": {
        "description": "Converts a time I into a list T representing local time: "
        "[year month day hour minute second isdst yearday weekday].",
        "name": "localtime",
        "section": "operator",
        "signature": "I  ->  T",
    },
    "log": {
        "description": "G is the natural logarithm of F.",
        "name": "log",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "log10": {
        "description": "G is the common logarithm of F.",
        "name": "log10",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "logical": {
        "description": "Tests whether X is a logical.",
        "name": "logical",
        "section": "predicate",
        "signature": "X  ->  B",
    },
    "manual": {
        "description": "Writes this manual of all Joy primitives to output file.",
        "name": "manual",
        "section": "miscellaneous commands",
        "signature": "->",
    },
    "map": {
        "description": "Executes P on each member of aggregate A, collects results in sametype aggregate B.",
        "name": "map",
        "section": "combinator",
        "signature": "A [P]  ->  B",
    },
    "max": {
        "description": "N is the maximum of numeric values N1 and N2. Also supports float.",
        "name": "max",
        "section": "operator",
        "signature": "N1 N2  ->  N",
    },
    "maxint": {
        "description": "Pushes largest integer (platform dependent). Typically it is 32 bits.",
        "name": "maxint",
        "section": "operand",
        "signature": "->  maxint",
    },
    "min": {
        "description": "N is the minimum of numeric values N1 and N2. Also supports float.",
        "name": "min",
        "section": "operator",
        "signature": "N1 N2  ->  N",
    },
    "mktime": {
        "description": "Converts a list T representing local time into a time I.",
        "name": "mktime",
        "section": "operator",
        "signature": "T  ->  I",
    },
    "modf": {
        "description": "G is the fractional part and H is the integer part (but expressed as a float) of F.",
        "name": "modf",
        "section": "operator",
        "signature": "F  ->  G H",
    },
    "name": {
        "description": 'For operators and combinators, the string "sym" is the name of item sym, '
        "for literals sym the result string is its type.",
        "name": "name",
        "section": "operator",
        "signature": 'sym  ->  "sym"',
    },
    "neg": {
        "description": "Integer J is the negative of integer I. Also supports float.",
        "name": "neg",
        "section": "operator",
        "signature": "I  ->  J",
    },
    "not": {
        "description": "Y is the complement of set X, logical negation for truth values.",
        "name": "not",
        "section": "operator",
        "signature": "X  ->  Y",
    },
    "null": {
        "description": "Tests for empty aggregate X or zero numeric.",
        "name": "null",
        "section": "predicate",
        "signature": "X  ->  B",
    },
    "nullary": {
        "description": "Executes P, which leaves R on top of the stack. "
        "No matter how many parameters this consumes, none are removed from the stack.",
        "name": "nullary",
        "section": "combinator",
        "signature": "[P]  ->  R",
    },
    "of": {
        "description": "X (= A[I]) is the I-th member of aggregate A.",
        "name": "of",
        "section": "operator",
        "signature": "I A  ->  X",
    },
    "opcase": {
        "description": "Indexing on type of X, returns the list [Xs].",
        "name": "opcase",
        "section": "operator",
        "signature": "X [..[X Xs]..]  ->  [Xs]",
    },
    "or": {
        "description": "Z is the union of sets X and Y, logical disjunction for truth values.",
        "name": "or",
        "section": "operator",
        "signature": "X Y  ->  Z",
    },
    "ord": {
        "description": "Integer I is the Ascii value of character C (or logical or integer).",
        "name": "ord",
        "section": "operator",
        "signature": "C  ->  I",
    },
    "pop": {
        "description": "Removes X from top of the stack.",
        "name": "pop",
        "section": "operator",
        "signature": "X  ->",
    },
    "popd": {
        "description": "As if defined by: popd == [pop] dip",
        "name": "popd",
        "section": "operator",
        "signature": "Y Z  ->  Z",
    },
    "pow": {
        "description": "H is F raised to the Gth power.",
        "name": "pow",
        "section": "operator",
        "signature": "F G  ->  H",
    },
    "pred": {
        "description": "Numeric N is the predecessor of numeric M.",
        "name": "pred",
        "section": "operator",
        "signature": "M  ->  N",
    },
    "primrec": {
        "description": "Executes I to obtain an initial value R0. "
        "For integer X uses increasing positive integers to X, combines by C for new R. "
        "For aggregate X uses successive members and combines by C for new R.",
        "name": "primrec",
        "section": "combinator",
        "signature": "X [I] [C]  ->  R",
    },
    "put": {
        "description": "Writes X to output, pops X off stack.",
        "name": "put",
        "section": "miscellaneous commands",
        "signature": "X  ->",
    },
    "putch": {
        "description": "N: numeric, writes character whose ASCII is N.",
        "name": "putch",
        "section": "miscellaneous commands",
        "signature": "N  ->",
    },
    "putchars": {
        "description": "Writes abc.. (without quotes)",
        "name": "putchars",
        "section": "miscellaneous commands",
        "signature": '"abc.."  ->',
    },
    "quit": {
        "description": "Exit from Joy.",
        "name": "quit",
        "section": "miscellaneous commands",
        "signature": "->",
    },
    "rand": {
        "description": "I is a random integer.",
        "name": "rand",
        "section": "operand",
        "signature": "-> I",
    },
    "rem": {
        "description": "Integer K is the remainder of dividing I by J. Also supports float.",
        "name": "rem",
        "section": "operator",
        "signature": "I J  ->  K",
    },
    "rest": {
        "description": "R is the non-empty aggregate A with its first member removed.",
        "name": "rest",
        "section": "operator",
        "signature": "A  ->  R",
    },
    "rolldown": {
        "description": "Moves Y and Z down, moves X up",
        "name": "rolldown",
        "section": "operator",
        "signature": "X Y Z  ->  Y Z X",
    },
    "rolldownd": {
        "description": "As if defined by: rolldownd == [rolldown] dip",
        "name": "rolldownd",
        "section": "operator",
        "signature": "X Y Z W  ->  Y Z X W",
    },
    "rollup": {
        "description": "Moves X and Y up, moves Z down",
        "name": "rollup",
        "section": "operator",
        "signature": "X Y Z  ->  Z X Y",
    },
    "rollupd": {
        "description": "As if defined by: rollupd == [rollup] dip",
        "name": "rollupd",
        "section": "operator",
        "signature": "X Y Z W  ->  Z X Y W",
    },
    "rotate": {
        "description": "Interchanges X and Z",
        "name": "rotate",
        "section": "operator",
        "signature": "X Y Z  ->  Z Y X",
    },
    "rotated": {
        "description": "As if defined by: rotated == [rotate] dip",
        "name": "rotated",
        "section": "operator",
        "signature": "X Y Z W  ->  Z Y X W",
    },
    "set": {
        "description": "Tests whether X is a set.",
        "name": "set",
        "section": "predicate",
        "signature": "X  ->  B",
    },
    "setautoput": {
        "description": "Sets value of flag for automatic put to I (if I = 0, none; if I = 1, put; if I = 2, stack.",
        "name": "setautoput",
        "section": "miscellaneous commands",
        "signature": "I  ->",
    },
    "setecho": {
        "description": "Sets value of echo flag for listing. I = 0: no echo, 1: echo, 2: with tab, 3: and linenumber.",
        "name": "setecho",
        "section": "miscellaneous commands",
        "signature": "I ->",
    },
    "setsize": {
        "description": "Pushes the maximum number of elements in a set (platform dependent). "
        "Typically it is 32, and set members are in the range 0..31.",
        "name": "setsize",
        "section": "operand",
        "signature": "->  setsize",
    },
    "setundeferror": {
        "description": "Sets flag that controls behavior of undefined functions (0 = no error, 1 = error).",
        "name": "setundeferror",
        "section": "miscellaneous commands",
        "signature": "I  ->",
    },
    "sign": {
        "description": "Integer N2 is the sign (-1 or 0 or +1) of integer N1, "
        "or float N2 is the sign (-1.0 or 0.0 or 1.0) of float N1.",
        "name": "sign",
        "section": "operator",
        "signature": "N1  ->  N2",
    },
    "sin": {
        "description": "G is the sine of F.",
        "name": "sin",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "sinh": {
        "description": "G is the hyperbolic sine of F.",
        "name": "sinh",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "size": {
        "description": "Integer I is the number of elements of aggregate A.",
        "name": "size",
        "section": "operator",
        "signature": "A  ->  I",
    },
    "small": {
        "description": "Tests whether aggregate X has 0 or 1 members, or numeric 0 or 1.",
        "name": "small",
        "section": "predicate",
        "signature": "X  ->  B",
    },
    "some": {
        "description": "Applies test B to members of aggregate A, X = true if some pass.",
        "name": "some",
        "section": "combinator",
        "signature": "A  [B]  ->  X",
    },
    "split": {
        "description": "Uses test B to split aggregate A into sametype aggregates A1 and A2.",
        "name": "split",
        "section": "combinator",
        "signature": "A [B]  ->  A1 A2",
    },
    "sqrt": {
        "description": "G is the square root of F.",
        "name": "sqrt",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "srand": {
        "description": "Sets the random integer seed to integer I.",
        "name": "srand",
        "section": "operator",
        "signature": "I  ->",
    },
    "stack": {
        "description": "Pushes the stack as a list.",
        "name": "stack",
        "section": "operand",
        "signature": ".. X Y Z  ->  .. X Y Z [Z Y X ..]",
    },
    "stderr": {
        "description": "Pushes the standard error stream.",
        "name": "stderr",
        "section": "operand",
        "signature": "->  S",
    },
    "stdin": {
        "description": "Pushes the standard input stream.",
        "name": "stdin",
        "section": "operand",
        "signature": "->  S",
    },
    "stdout": {
        "description": "Pushes the standard output stream.",
        "name": "stdout",
        "section": "operand",
        "signature": "->  S",
    },
    "step": {
        "description": "Sequentially putting members of aggregate A onto stack, executes P for each member of A.",
        "name": "step",
        "section": "combinator",
        "signature": "A  [P]  ->  ...",
    },
    "strftime": {
        "description": "Formats a list T in the format of localtime or gmtime using string S1 and pushes the result S2.",
        "name": "strftime",
        "section": "operator",
        "signature": "T S1  ->  S2",
    },
    "string": {
        "description": "Tests whether X is a string.",
        "name": "string",
        "section": "predicate",
        "signature": "X  ->  B",
    },
    "strtod": {
        "description": "String S is converted to the float R.",
        "name": "strtod",
        "section": "operator",
        "signature": "S  ->  R",
    },
    "strtol": {
        "description": "String S is converted to the integer J using base I. "
        'If I = 0, assumes base 10, but leading "0" means base 8 and leading "0x" means base 16.',
        "name": "strtol",
        "section": "operator",
        "signature": "S I  ->  J",
    },
    "succ": {
        "description": "Numeric N is the successor of numeric M.",
        "name": "succ",
        "section": "operator",
        "signature": "M  ->  N",
    },
    "swap": {
        "description": "Interchanges X and Y on top of the stack.",
        "name": "swap",
        "section": "operator",
        "signature": "X Y  ->   Y X",
    },
    "swapd": {
        "description": "As if defined by: swapd == [swap] dip",
        "name": "swapd",
        "section": "operator",
        "signature": "X Y Z  ->  Y X Z",
    },
    "swons": {
        "description": "Aggregate B is A with a new member X (first member for sequences).",
        "name": "swons",
        "section": "operator",
        "signature": "A X  ->  B",
    },
    "system": {
        "description": 'Escapes to shell, executes string "command". '
        "The string may cause execution of another program. "
        "When that has finished, the process returns to Joy.",
        "name": "system",
        "section": "miscellaneous commands",
        "signature": '"command"  ->',
    },
    "tailrec": {
        "description": "Executes P. If that yields true, executes T. Else executes R1, recurses.",
        "name": "tailrec",
        "section": "combinator",
        "signature": "[P] [T] [R1]  ->  ...",
    },
    "take": {
        "description": "Aggregate B is the result of retaining just the first N elements of A.",
        "name": "take",
        "section": "operator",
        "signature": "A N  ->  B",
    },
    "tan": {
        "description": "G is the tangent of F.",
        "name": "tan",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "tanh": {
        "description": "G is the hyperbolic tangent of F.",
        "name": "tanh",
        "section": "operator",
        "signature": "F  ->  G",
    },
    "ternary": {
        "description": "Executes P, which leaves R on top of the stack. "
        "No matter how many parameters this consumes, exactly three are removed from the stack.",
        "name": "ternary",
        "section": "combinator",
        "signature": "X Y Z [P]  ->  R",
    },
    "time": {
        "description": "Pushes the current time (in seconds since the Epoch).",
        "name": "time",
        "section": "operand",
        "signature": "->  I",
    },
    "times": {
        "description": "N times executes P.",
        "name": "times",
        "section": "combinator",
        "signature": "N [P]  ->  ...",
    },
    "treegenrec": {
        "description": "T is a tree. If T is a leaf, executes O1. Else executes O2 and then [[O1] [O2] [C] treegenrec] C.",
        "name": "treegenrec",
        "section": "combinator",
        "signature": "T [O1] [O2] [C]  ->  ...",
    },
    "treerec": {
        "description": "T is a tree. If T is a leaf, executes O. Else executes [[O] [C] treerec] C.",
        "name": "treerec",
        "section": "combinator",
        "signature": "T [O] [C]  ->  ...",
    },
    "treestep": {
        "description": "Recursively traverses leaves of tree T, executes P for each leaf.",
        "name": "treestep",
        "section": "combinator",
        "signature": "T [P]  ->  ...",
    },
    "true": {
        "description": "Pushes the value true.",
        "name": "true",
        "section": "operand",
        "signature": "->  true",
    },
    "trunc": {
        "description": "I is an integer equal to the float F truncated toward zero.",
        "name": "trunc",
        "section": "operator",
        "signature": "F  ->  I",
    },
    "unary": {
        "description": "Executes P, which leaves R on top of the stack. "
        "No matter how many parameters this consumes, exactly one is removed from the stack.",
        "name": "unary",
        "section": "combinator",
        "signature": "X [P]  ->  R",
    },
    "unary2": {
        "description": "Executes P twice, with X1 and X2 on top of the stack. Returns the two values R1 and R2.",
        "name": "unary2",
        "section": "combinator",
        "signature": "X1 X2 [P]  ->  R1 R2",
    },
    "unary3": {
        "description": "Executes P three times, with Xi, returns Ri (i = 1..3).",
        "name": "unary3",
        "section": "combinator",
        "signature": "X1 X2 X3 [P]  ->  R1 R2 R3",
    },
    "unary4": {
        "description": "Executes P four times, with Xi, returns Ri (i = 1..4).",
        "name": "unary4",
        "section": "combinator",
        "signature": "X1 X2 X3 X4 [P]  ->  R1 R2 R3 R4",
    },
    "uncons": {
        "description": "F and R are the first and the rest of non-empty aggregate A.",
        "name": "uncons",
        "section": "operator",
        "signature": "A  ->  F R",
    },
    "undeferror": {
        "description": "Pushes current value of undefined-is-error flag.",
        "name": "undeferror",
        "section": "operand",
        "signature": "->  I",
    },
    "undefs": {
        "description": "Push a list of all undefined symbols in the current symbol table.",
        "name": "undefs",
        "section": "operand",
        "signature": "->",
    },
    "unstack": {
        "description": "The list [X Y ..] becomes the new stack.",
        "name": "unstack",
        "section": "operator",
        "signature": "[X Y ..]  ->  ..Y X",
    },
    "unswons": {
        "description": "R and F are the rest and the first of non-empty aggregate A.",
        "name": "unswons",
        "section": "operator",
        "signature": "A  ->  R F",
    },
    "user": {
        "description": "Tests whether X is a user-defined symbol.",
        "name": "user",
        "section": "predicate",
        "signature": "X  ->  B",
    },
    "while": {
        "description": "While executing B yields true executes D.",
        "name": "while",
        "section": "combinator",
        "signature": "[B] [D]  ->  ...",
    },
    "x": {
        "description": "Executes P without popping [P]. So, [P] x == [P] P.",
        "name": "x",
        "section": "combinator",
        "signature": "[P]  ->  ...",
    },
    "xor": {
        "description": "Z is the symmetric difference of sets X and Y, logical exclusive disjunction for truth values.",
        "name": "xor",
        "section": "operator",
        "signature": "X Y  ->  Z",
    },
}

SECTIONS: Dict[str, List[str]] = {
    "operand": [
        "false",
        "true",
        "maxint",
        "setsize",
        "stack",
        "conts",
        "autoput",
        "undeferror",
        "undefs",
        "echo",
        "clock",
        "time",
        "rand",
        "stdin",
        "stdout",
        "stderr",
    ],
    "operator": [
        "id",
        "dup",
        "swap",
        "rollup",
        "rolldown",
        "rotate",
        "popd",
        "dupd",
        "swapd",
        "rollupd",
        "rolldownd",
        "rotated",
        "pop",
        "choice",
        "or",
        "xor",
        "and",
        "not",
        "+",
        "-",
        "*",
        "/",
        "rem",
        "div",
        "sign",
        "neg",
        "ord",
        "chr",
        "abs",
        "acos",
        "asin",
        "atan",
        "atan2",
        "ceil",
        "cos",
        "cosh",
        "exp",
        "floor",
        "frexp",
        "ldexp",
        "log",
        "log10",
        "modf",
        "pow",
        "sin",
        "sinh",
        "sqrt",
        "tan",
        "tanh",
        "trunc",
        "localtime",
        "gmtime",
        "mktime",
        "strftime",
        "strtol",
        "strtod",
        "format",
        "formatf",
        "srand",
        "pred",
        "succ",
        "max",
        "min",
        "fclose",
        "feof",
        "ferror",
        "fflush",
        "fgetch",
        "fgets",
        "fopen",
        "fread",
        "fwrite",
        "fremove",
        "frename",
        "fput",
        "fputch",
        "fputchars",
        "fputstring",
        "fseek",
        "ftell",
        "unstack",
        "cons",
        "swons",
        "first",
        "rest",
        "compare",
        "at",
        "of",
        "size",
        "opcase",
        "case",
        "uncons",
        "unswons",
        "drop",
        "take",
        "concat",
        "enconcat",
        "name",
        "intern",
        "body",
    ],
    "predicate": [
        "null",
        "small",
        ">=",
        ">",
        "<=",
        "<",
        "!=",
        "=",
        "equal",
        "has",
        "in",
        "integer",
        "char",
        "logical",
        "set",
        "string",
        "list",
        "leaf",
        "user",
        "float",
        "file",
    ],
    "combinator": [
        "i",
        "x",
        "dip",
        "app1",
        "app11",
        "app12",
        "construct",
        "nullary",
        "unary",
        "unary2",
        "unary3",
        "unary4",
        "app2",
        "app3",
        "app4",
        "binary",
        "ternary",
        "cleave",
        "branch",
        "ifte",
        "ifinteger",
        "ifchar",
        "iflogical",
        "ifset",
        "ifstring",
        "iflist",
        "iffloat",
        "iffile",
        "cond",
        "while",
        "linrec",
        "tailrec",
        "binrec",
        "genrec",
        "condlinrec",
        "step",
        "fold",
        "map",
        "times",
        "infra",
        "primrec",
        "filter",
        "split",
        "some",
        "all",
        "treestep",
        "treerec",
        "treegenrec",
    ],
    "miscellaneous commands": [
        "help",
        "helpdetail",
        "manual",
        "setautoput",
        "setundeferror",
        "setecho",
        "gc",
        "system",
        "getenv",
        "argv",
        "argc",
        "get",
        "put",
        "putch",
        "putchars",
        "include",
        "abort",
        "quit",
    ],
}

# =============================================================================
# Extensions (not in Joy manual but commonly used)
# =============================================================================

EXTENSIONS: Dict[str, Dict] = {
    ".": {
        "name": ".",
        "signature": "->",
        "description": "End of program/definition marker.",
        "section": "extension",
    },
    "putln": {
        "name": "putln",
        "signature": "X ->",
        "description": "Writes X to output followed by newline.",
        "section": "extension",
    },
    "swoncat": {
        "name": "swoncat",
        "signature": "A B -> C",
        "description": "Swap then concat. Equivalent to: swap concat",
        "section": "extension",
    },
    "condnestrec": {
        "name": "condnestrec",
        "signature": "[[C1] [C2] .. [D]] -> ...",
        "description": "Conditional nested recursion. Each clause [Ci] is [[B] [T]] or [[B] [R1] [R2] ...].",
        "section": "extension",
    },
    "__settracegc": {
        "name": "__settracegc",
        "signature": "I ->",
        "description": "Debug: set GC tracing level (no-op).",
        "section": "extension",
    },
    "newline": {
        "name": "newline",
        "signature": "->",
        "description": "Outputs a newline character.",
        "section": "extension",
    },
}

# =============================================================================
# Utility Functions
# =============================================================================


def is_primitive(name: str) -> bool:
    """Check if name is a known Joy primitive."""
    return name in PRIMITIVES or name in EXTENSIONS


def get_signature(name: str) -> Optional[str]:
    """Get the stack signature for a primitive."""
    if name in PRIMITIVES:
        return PRIMITIVES[name]["signature"]
    if name in EXTENSIONS:
        return EXTENSIONS[name]["signature"]
    return None


def get_help(name: str) -> Optional[str]:
    """Get help text for a primitive.

    Returns formatted help string or None if not found.
    """
    if name in PRIMITIVES:
        p = PRIMITIVES[name]
        return f"{name} : {p['signature']}\n\n{p['description']}\n\nSection: {p['section']}"
    if name in EXTENSIONS:
        p = EXTENSIONS[name]
        return f"{name} : {p['signature']}\n\n{p['description']}\n\nSection: {p['section']}"
    return None


def list_primitives(section: Optional[str] = None) -> List[str]:
    """List all primitives, optionally filtered by section."""
    if section:
        return SECTIONS.get(section, [])
    return list(PRIMITIVES.keys())


def list_sections() -> List[str]:
    """List all primitive sections."""
    return list(SECTIONS.keys())


def check_coverage(implemented: Set[str]) -> Tuple[Set[str], Set[str], Set[str]]:
    """Check which primitives are implemented.

    Args:
        implemented: Set of primitive names that are implemented

    Returns:
        Tuple of (missing, extra, covered) sets
    """
    required = set(PRIMITIVES.keys())
    missing = required - implemented
    extra = implemented - required
    covered = required & implemented
    return missing, extra, covered


def coverage_report(implemented: Set[str]) -> str:
    """Generate a coverage report."""
    missing, extra, covered = check_coverage(implemented)

    lines = [
        "Joy Primitives Coverage Report",
        "=" * 40,
        "",
        f"Total in spec: {len(PRIMITIVES)}",
        f"Implemented:   {len(covered)} ({100 * len(covered) // len(PRIMITIVES)}%)",
        f"Missing:       {len(missing)}",
        f"Extensions:    {len(extra)}",
        "",
    ]

    if missing:
        lines.append("Missing by section:")
        for section, prims in SECTIONS.items():
            section_missing = [p for p in prims if p in missing]
            if section_missing:
                lines.append(f"\n  {section} ({len(section_missing)}):")
                for p in section_missing:
                    sig = PRIMITIVES[p]["signature"]
                    lines.append(f"    {p}: {sig}")

    if extra:
        lines.append("\nExtensions/extras:")
        known_ext = extra & set(EXTENSIONS.keys())
        unknown = extra - known_ext
        if known_ext:
            lines.append("  Known extensions:")
            for p in sorted(known_ext):
                lines.append(f"    {p}")
        if unknown:
            lines.append("  Unknown (may need documentation):")
            for p in sorted(unknown):
                lines.append(f"    {p}")

    return "\n".join(lines)


# Priority primitives - commonly used, should be implemented first
PRIORITY_PRIMITIVES = [
    # Core stack ops
    "id",
    "dup",
    "swap",
    "pop",
    "popd",
    "dupd",
    "swapd",
    "rollup",
    "rolldown",
    "rotate",
    # Arithmetic
    "+",
    "-",
    "*",
    "/",
    "rem",
    "neg",
    "abs",
    "succ",
    "pred",
    "max",
    "min",
    # Comparison
    "<",
    "<=",
    "=",
    "!=",
    ">",
    ">=",
    # Logic
    "and",
    "or",
    "not",
    "xor",
    # Predicates
    "null",
    "small",
    "integer",
    "char",
    "logical",
    "string",
    "list",
    "set",
    "float",
    # List ops
    "first",
    "rest",
    "cons",
    "swons",
    "uncons",
    "concat",
    "size",
    "at",
    "drop",
    "take",
    # Combinators
    "i",
    "x",
    "dip",
    "ifte",
    "branch",
    "cond",
    "map",
    "fold",
    "filter",
    "step",
    "times",
    "linrec",
    "tailrec",
    "binrec",
    "genrec",
    "primrec",
    # I/O
    "put",
    "putch",
    "putchars",
    "get",
    # Control
    "while",
    "choice",
    # Meta
    "stack",
    "unstack",
]


if __name__ == "__main__":
    print("Joy Primitives Module")
    print(f"Loaded {len(PRIMITIVES)} primitives in {len(SECTIONS)} sections")
    print()
    for name in ["dup", "ifte", "map"]:
        print(get_help(name))
        print()
