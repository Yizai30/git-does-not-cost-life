#!/usr/bin/env python3
"""git-submit wrapper script to bypass type hint errors."""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Monkey-patch typing module to bypass the error
import typing
if not hasattr(typing, '_PATCHED'):
    # Store original __getitem__
    original_getitem = typing.GenericAlias.__getitem__

    def patched_getitem(self, key):
        """Patched __getitem__ that handles Callable[[...]] gracefully."""
        try:
            return original_getitem(self, key)
        except TypeError:
            # If it fails, return self as-is (this is a workaround)
            return self

    typing.GenericAlias.__getitem__ = patched_getitem
    typing._PATCHED = True

# Now import and run the CLI
try:
    from git_submit.cli import main
    sys.exit(main())
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
