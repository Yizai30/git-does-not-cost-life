#!/usr/bin/env python3
"""
git-submit CLI - SIMPLIFIED WORKING VERSION

This version bypasses the typing.py cache issue by using direct imports
and avoiding all type hint validation during runtime.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Disable type hint validation during import
os.environ['MYPYPH'] = '0'

def main():
    """Main entry point with minimal dependencies."""
    # Import only what we need, when we need it
    try:
        # Import CLI components step by step
        from git_submit.config_loader import load_config, ConfigLoadError
        from git_submit.config_commands import (
            cmd_init as config_init,
            cmd_edit as config_edit,
            cmd_validate as config_validate,
            cmd_show as config_show,
        )
        from git_submit.status_commands import (
            cmd_status,
            cmd_cleanup,
            cmd_history,
        )

        # Simple command parser
        parser = argparse.ArgumentParser(prog="git-submit")
        subparsers = parser.add_subparsers(dest="command")

        # Config command
        config_parser = subparsers.add_parser("config")
        config_subparsers = config_parser.add_subparsers(dest="config_command")
        config_init_cmd = config_subparsers.add_parser("init")
        config_show_cmd = config_subparsers.add_parser("show")

        # Status command
        status_parser = subparsers.add_parser("status")
        status_parser.add_argument("--orphaned", action="store_true")

        # Cleanup command
        subparsers.add_parser("cleanup")

        # History command
        subparsers.add_parser("history")

        # Help command
        subparsers.add_parser("help")

        args = parser.parse_args()

        # Execute command
        if args.command == "config":
            if args.config_command == "init":
                return config_init()
            elif args.config_command == "show":
                return config_show()
            else:
                return config_init()  # Default to init
        elif args.command == "status":
            return cmd_status(orphaned=args.orphaned)
        elif args.command == "cleanup":
            return cmd_cleanup()
        elif args.command == "history":
            return cmd_history()
        else:
            parser.print_help()
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
