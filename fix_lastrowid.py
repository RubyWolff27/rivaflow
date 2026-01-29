#!/usr/bin/env python3
"""
Script to fix cursor.lastrowid issues for PostgreSQL compatibility.
Replaces lastrowid pattern with RETURNING id clause for PostgreSQL.
"""

import re
from pathlib import Path

def fix_lastrowid_in_file(filepath):
    """Fix lastrowid usage in a single repository file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Pattern 1: Direct return of lastrowid
    # Replace: return cursor.lastrowid
    # With: RETURNING id logic

    # Pattern 2: Assignment then use
    # Replace: var_id = cursor.lastrowid
    # With: RETURNING id logic

    # Check if file already has DB_TYPE import
    has_db_type_import = 'from rivaflow.db.database import DB_TYPE' in content

    # Find all INSERT statements followed by lastrowid
    # This regex finds: cursor.execute(...INSERT...) followed by lastrowid usage

    modifications = []

    # Find simple pattern: some_id = cursor.lastrowid
    pattern = r'(\s+)(\w+_id)\s*=\s*cursor\.lastrowid'
    matches = list(re.finditer(pattern, content))

    if matches:
        print(f"Found {len(matches)} lastrowid patterns in {filepath.name}")

        # Add import if needed
        if not has_db_type_import:
            # Add import after existing imports
            import_pattern = r'(from rivaflow\.db\.database import get_connection)'
            content = re.sub(
                import_pattern,
                r'\1, DB_TYPE',
                content
            )

        # Replace each occurrence
        for match in reversed(matches):  # Reverse to maintain positions
            indent = match.group(1)
            var_name = match.group(2)

            replacement = f'''{indent}# PostgreSQL: use RETURNING clause, SQLite: use lastrowid
{indent}from rivaflow.db.database import DB_TYPE as _DB_TYPE
{indent}if _DB_TYPE == "postgresql":
{indent}    result = cursor.fetchone()
{indent}    if hasattr(result, 'keys'):
{indent}        {var_name} = result['id']
{indent}    else:
{indent}        {var_name} = result[0]
{indent}else:
{indent}    {var_name} = cursor.lastrowid'''

            start = match.start()
            end = match.end()
            content = content[:start] + replacement + content[end:]

    # Find direct return pattern: return cursor.lastrowid
    pattern2 = r'(\s+)return cursor\.lastrowid'
    matches2 = list(re.finditer(pattern2, content))

    if matches2:
        print(f"Found {len(matches2)} direct return lastrowid in {filepath.name}")

        for match in reversed(matches2):
            indent = match.group(1)

            replacement = f'''{indent}# PostgreSQL: use RETURNING clause, SQLite: use lastrowid
{indent}from rivaflow.db.database import DB_TYPE as _DB_TYPE
{indent}if _DB_TYPE == "postgresql":
{indent}    result = cursor.fetchone()
{indent}    if hasattr(result, 'keys'):
{indent}        return result['id']
{indent}    else:
{indent}        return result[0]
{indent}else:
{indent}    return cursor.lastrowid'''

            start = match.start()
            end = match.end()
            content = content[:start] + replacement + content[end:]

    # Write back
    if matches or matches2:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✓ Fixed {filepath.name}")
        return True

    return False

# Files to fix (excluding already fixed ones)
repo_dir = Path("rivaflow/db/repositories")
files_to_skip = {"user_repo.py", "refresh_token_repo.py", "__init__.py"}

fixed_count = 0
for filepath in repo_dir.glob("*.py"):
    if filepath.name not in files_to_skip:
        if fix_lastrowid_in_file(filepath):
            fixed_count += 1

print(f"\nFixed {fixed_count} files total")
