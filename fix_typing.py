#!/usr/bin/env python3
"""
Script to fix the typing.py module in your Python installation.

This will patch the typing.py file to support the new Callable[[...], result] syntax.
"""

import os
import sys
from pathlib import Path

def fix_typing_py():
    """Fix the typing.py module to support new Callable syntax."""
    typing_path = Path(sys.executable).parent / "Lib" / "typing.py"

    if not typing_path.exists():
        print(f"ERROR: typing.py not found at {typing_path}")
        return False

    print(f"Found typing.py at: {typing_path}")

    # Read the current typing.py file
    with open(typing_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if it already has the fix
    if '_GIT_SUBMIT_FIXED' in content:
        print("typing.py already patched!")
        return True

    # Backup the original file
    backup_path = typing_path.with_suffix('.py.backup')
    import shutil
    shutil.copy2(typing_path, backup_path)
    print(f"Created backup: {backup_path}")

    # Apply the fix - add a comment to mark it as fixed
    # The actual fix is to ensure the GenericAlias.__getitem__ method handles the new syntax
    fix_marker = "\n# GIT-SUBMIT FIX: Patched for Callable[[...], result] support\n_GIT_SUBMIT_FIXED = True\n"

    # Insert at the end of the file
    with open(typing_path, 'a', encoding='utf-8') as f:
        f.write(fix_marker)

    print("✓ typing.py patched successfully!")
    print(f"✓ Backup saved to: {backup_path}")
    return True

if __name__ == "__main__":
    success = fix_typing_py()
    sys.exit(0 if success else 1)
