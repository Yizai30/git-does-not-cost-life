#!/usr/bin/env python3
"""
git-submit CLI - FULL WORKING VERSION (Windows compatible)

This version includes all commands and fixes Windows encoding issues.
"""

import os
import sys
import argparse
from pathlib import Path
import time
import subprocess

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_git_available():
    """Check if git is available."""
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_current_branch():
    """Get current git branch."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None

def execute_push(remote, branch, all_branches=False, force=False, dry_run=False):
    """Execute git push with retry logic."""
    git_cmd = ["git", "push"]

    if all_branches:
        git_cmd.append("--all")
    else:
        git_cmd.extend([remote, branch])

    if force:
        git_cmd.append("--force")

    if dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(git_cmd)}")
        return True

    print(f"Executing: {' '.join(git_cmd)}")

    try:
        result = subprocess.run(
            git_cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print("\n[OK] Push successful!")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"\n[ERROR] Push failed (exit code {result.returncode})")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"\n[ERROR] Error executing git push: {e}")
        return False

def main():
    """Main entry point."""
    try:
        # Import CLI components
        from git_submit.config_loader import load_config
        from git_submit.config_commands import (
            cmd_init as config_init,
            cmd_show as config_show,
        )
        from git_submit.status_commands import (
            cmd_status,
            cmd_cleanup,
            cmd_history,
        )

        # Command parser
        parser = argparse.ArgumentParser(
            prog="git-submit",
            description="Automated git push with infinite retry logic"
        )
        subparsers = parser.add_subparsers(dest="command")

        # Config command
        config_parser = subparsers.add_parser("config")
        config_subparsers = config_parser.add_subparsers(dest="config_command")
        config_init_cmd = config_subparsers.add_parser("init")
        config_show_cmd = config_subparsers.add_parser("show")

        # Push command
        push_parser = subparsers.add_parser("push", help="Push to git with automatic retries")
        push_parser.add_argument("--remote", default="origin", help="Remote to push to")
        push_parser.add_argument("--branch", help="Branch to push")
        push_parser.add_argument("--all", action="store_true", help="Push all branches")
        push_parser.add_argument("--force", "-f", action="store_true", help="Force push")
        push_parser.add_argument("--dry-run", action="store_true", help="Validate without pushing")
        push_parser.add_argument("--notify-desktop", action="store_true", help="Enable desktop notifications")
        push_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

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
                return config_init()
        elif args.command == "push":
            # Check git availability
            if not check_git_available():
                print("[ERROR] Git not found. Install from https://git-scm.com/")
                return 1

            # Determine branch
            branch = args.branch
            if not branch:
                branch = get_current_branch()
                if not branch:
                    print("[ERROR] Not in a git repository or cannot detect branch")
                    return 1

            print(f"\nPushing to {args.remote}/{branch}...")
            if args.dry_run:
                print("[DRY RUN MODE - No actual push will be performed]")

            # Execute push with simple retry logic
            max_retries = 100  # Safety limit
            retry_delay = 5

            for attempt in range(1, max_retries + 1):
                print(f"\nAttempt {attempt}...")

                success = execute_push(
                    remote=args.remote,
                    branch=branch,
                    all_branches=args.all,
                    force=args.force,
                    dry_run=args.dry_run
                )

                if success:
                    if not args.dry_run:
                        print(f"\n[OK] Push successful on attempt {attempt}!")

                        # Desktop notification
                        if args.notify_desktop:
                            try:
                                from plyer import notification
                                notification.notify(
                                    title="GitHub Push Successful",
                                    message=f"{args.remote}/{branch}",
                                    timeout=10
                                )
                                print("[OK] Desktop notification sent")
                            except Exception as e:
                                if args.verbose:
                                    print(f"[WARNING] Desktop notification failed: {e}")
                    return 0
                else:
                    if attempt < max_retries:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        # Exponential backoff
                        retry_delay = min(retry_delay * 2, 300)

            print(f"\n[ERROR] Push failed after {max_retries} attempts")
            return 1

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
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
