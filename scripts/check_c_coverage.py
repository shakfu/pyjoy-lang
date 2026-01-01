#!/usr/bin/env python3
"""
Check Joy primitives coverage in the C backend.
"""

import re
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pyjoy.primitives import check_coverage, coverage_report, PRIMITIVES, SECTIONS


def get_c_backend_primitives() -> set:
    """Extract primitive names from C backend."""
    c_file = Path(__file__).parent.parent / 'src' / 'pyjoy' / 'backends' / 'c' / 'runtime' / 'joy_primitives.c'

    if not c_file.exists():
        print(f"Error: {c_file} not found")
        sys.exit(1)

    content = c_file.read_text()

    # Find all joy_dict_define_primitive calls
    pattern = r'joy_dict_define_primitive\(d,\s*"([^"]+)"'
    matches = re.findall(pattern, content)

    return set(matches)


def main():
    implemented = get_c_backend_primitives()

    print(coverage_report(implemented))

    # Also show priority primitives status
    print("\n" + "=" * 40)
    print("Priority Primitives Status")
    print("=" * 40)

    from pyjoy.primitives import PRIORITY_PRIMITIVES

    missing_priority = [p for p in PRIORITY_PRIMITIVES if p not in implemented]
    if missing_priority:
        print(f"\nMissing priority primitives ({len(missing_priority)}):")
        for p in missing_priority:
            if p in PRIMITIVES:
                sig = PRIMITIVES[p]['signature']
                print(f"  {p}: {sig}")
            else:
                print(f"  {p}: (not in spec)")
    else:
        print("\nAll priority primitives implemented!")


if __name__ == '__main__':
    main()
