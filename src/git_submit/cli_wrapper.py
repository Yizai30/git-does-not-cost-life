"""CLI wrapper that bypasses typing.py cache issues."""

import sys
import os
from pathlib import Path

# Determine correct paths
if __name__ == "__main__":
    # When run as script
    SCRIPT_DIR = Path(__file__).parent
else:
    # When imported
    SCRIPT_DIR = Path(__file__).parent

PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    """Main entry point that bypasses typing.py cache."""
    try:
        # Import CLI normally - Python will cache the module
        from git_submit.cli import main as cli_main
        return cli_main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
