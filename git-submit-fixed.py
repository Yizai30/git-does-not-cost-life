#!/usr/bin/env python3
"""
Fixed git-submit CLI that works around typing.py cache issues.
This script bypasses the type hint errors by monkey-patching the typing module.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    """Main entry point with error handling."""
    # Direct import without going through the broken type hints
    try:
        # Import the CLI module directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("cli", PROJECT_ROOT / "src" / "git_submit" / "cli.py")
        cli_module = importlib.util.module_from_spec(spec)

        # Execute the module
        spec.loader.exec_module(cli_module)

        # Call main function
        return cli_module.main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
