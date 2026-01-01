#!/usr/bin/env python3
"""
Parse the Joy manual (docs/joy-manual.txt) and extract primitive entries.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional


def parse_joy_manual(file_path: str) -> Dict:
    """
    Parse the Joy manual file and return a dictionary of primitive entries.

    Returns:
        dict: A dictionary with the following structure:
            {
                'sections': {
                    'operand': ['false', 'true', ...],
                    'operator': ['id', 'dup', ...],
                    ...
                },
                'primitives': {
                    'dup': {
                        'name': 'dup',
                        'signature': 'X  ->   X X',
                        'description': 'Pushes an extra copy of X onto stack.',
                        'section': 'operator'
                    },
                    ...
                }
            }
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {
        'sections': {},
        'primitives': {}
    }

    # Split into sections
    section_pattern = re.compile(r'\n\n\n(\w[\w\s]*)\n\n', re.MULTILINE)

    # Find all sections
    sections = ['operand', 'operator', 'predicate', 'combinator', 'miscellaneous commands']

    for section_name in sections:
        # Find section start
        section_match = re.search(rf'\n{re.escape(section_name)}\n', content)
        if not section_match:
            continue

        section_start = section_match.end()

        # Find next section or end
        next_section = None
        for other in sections:
            if other == section_name:
                continue
            match = re.search(rf'\n{re.escape(other)}\n', content[section_start:])
            if match:
                if next_section is None or match.start() < next_section:
                    next_section = match.start()

        if next_section:
            section_content = content[section_start:section_start + next_section]
        else:
            section_content = content[section_start:]

        # Parse entries in this section
        parse_section_entries(section_content, section_name, result)

    return result


def parse_section_entries(section_content: str, section_name: str, result: Dict):
    """Parse entries from a section's content."""

    if section_name not in result['sections']:
        result['sections'][section_name] = []

    # Pattern to match entry lines: name : signature
    # Entry names can contain special chars like +, -, *, /, <, >, =, !
    # The name is followed by multiple spaces, then :, then the signature
    entry_pattern = re.compile(r'^(\S+)\s+:\s+(.+)$', re.MULTILINE)

    lines = section_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Try to match an entry
        match = entry_pattern.match(line)
        if match:
            name = match.group(1).strip()
            signature = match.group(2).strip()

            # Skip type descriptions (entries ending with "type")
            if name.endswith('type'):
                i += 1
                continue

            # Collect description lines
            description_lines = []
            i += 1
            while i < len(lines):
                desc_line = lines[i]
                # Stop if we hit another entry or empty line followed by entry
                if not desc_line.strip():
                    # Check if next non-empty line is an entry
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines) and entry_pattern.match(lines[j]):
                        break
                    i += 1
                    continue
                if entry_pattern.match(desc_line):
                    break
                description_lines.append(desc_line.strip())
                i += 1

            description = ' '.join(description_lines)

            # Save entry
            result['primitives'][name] = {
                'name': name,
                'signature': signature,
                'description': description,
                'section': section_name
            }
            result['sections'][section_name].append(name)
        else:
            i += 1


def generate_primitives_dict(parsed: Dict) -> Dict[str, Dict]:
    """Generate a simplified primitives dictionary."""
    return parsed['primitives']


def main():
    """Main function to parse and display the manual."""
    import sys

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    manual_path = project_root / 'docs' / 'joy-manual.txt'
    if len(sys.argv) > 1:
        manual_path = Path(sys.argv[1])

    if not manual_path.exists():
        print(f"Error: {manual_path} not found")
        sys.exit(1)

    print(f"Parsing {manual_path}...")
    parsed = parse_joy_manual(str(manual_path))

    # Print summary
    total = len(parsed['primitives'])
    print(f"\nFound {total} primitives across {len(parsed['sections'])} sections:")
    for section, entries in parsed['sections'].items():
        print(f"  {section}: {len(entries)} primitives")

    # Save to JSON
    output_path = project_root / 'docs' / 'joy_primitives.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {output_path}")

    # Also generate a simple name -> signature mapping
    simple_path = project_root / 'docs' / 'joy_primitives_simple.json'
    simple = {name: entry['signature'] for name, entry in parsed['primitives'].items()}
    with open(simple_path, 'w', encoding='utf-8') as f:
        json.dump(simple, f, indent=2, ensure_ascii=False)
    print(f"Saved simple mapping to {simple_path}")

    # Print some examples
    print("\nExample primitives:")
    examples = ['dup', 'swap', 'pop', 'i', 'ifte', 'map', 'fold', '+', '-', 'null']
    for name in examples:
        if name in parsed['primitives']:
            entry = parsed['primitives'][name]
            print(f"\n  {name} : {entry['signature']}")
            desc = entry['description'][:60] + '...' if len(entry['description']) > 60 else entry['description']
            print(f"    {desc}")


if __name__ == '__main__':
    main()
