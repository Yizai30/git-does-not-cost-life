"""Main CLI interface for git-submit."""

import asyncio
import os
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console (only if not already set)
if sys.platform == "win32":
    try:
        import locale
        if sys.stdout.encoding.lower() != 'utf-8':
            # Reconfigure console to use UTF-8
            import _locale
            _locale._getdefaultlocale = lambda *args: ['en_US', 'utf8']
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, Exception):
        # If reconfigure is not available, try legacy method
        try:
            import io
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except:
            pass

from git_submit.cli_args import parse_args, merge_args_with_config
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
from git_submit.git_wrapper import (
    check_git_available,
    get_current_branch,
    GitError,
)
from git_submit.state_manager import (
    create_state,
    save_state,
    delete_state,
    load_state,
    list_state_files,
    is_orphaned,
    generate_operation_id,
    OperationState,
)
from git_submit.retry_engine import RetryEngine, RetryState
from git_submit.log_handler import Logger, LogLevel, tail_log


def cmd_push(args, config) -> int:
    """Execute push with retry logic."""
    import time

    # Check git availability
    try:
        check_git_available()
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1

    # Validate config if notifications enabled
    if config.notifications.email.enabled:
        from git_submit.notifications import EmailNotifier
        email = EmailNotifier(
            enabled=config.notifications.email.enabled,
            smtp_host=config.notifications.email.smtp_host,
            smtp_port=config.notifications.email.smtp_port,
            username=config.notifications.email.username,
            password_env=config.notifications.email.password_env,
            from_address=config.notifications.email.from_address,
            to_address=config.notifications.email.to_address,
        )
        errors = email.validate()
        if errors:
            print("Email configuration errors:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            print("Fix config or disable email notifications.", file=sys.stderr)
            return 1

    # Determine repository path
    repo_path = os.getcwd()

    # Determine branch
    branch = args.branch if args.branch else config.git.branch
    if branch == "auto" or not branch:
        detected = get_current_branch()
        if not detected:
            print("Error: Not in a git repository or cannot detect branch", file=sys.stderr)
            return 1
        branch = detected

    # Determine remote
    remote = args.remote if args.remote else config.git.remote

    # Generate operation ID
    operation_id = generate_operation_id(repo_path, branch)

    # Create logger
    logger = Logger(
        operation_id=operation_id,
        verbose=args.verbose,
        quiet=args.quiet,
        json_output=args.json,
    )

    logger.info("Starting push operation", repository=repo_path, branch=branch)

    # Check for existing state (resume)
    existing_state = load_state(operation_id)
    if existing_state:
        logger.info("Resuming from previous operation", attempts=existing_state.attempts)
        # Convert OperationState to RetryState
        retry_state = RetryState(
            attempt=existing_state.attempts,
            last_error=existing_state.last_error,
            started_at=time.mktime(time.strptime(existing_state.started_at, "%Y-%m-%dT%H:%M:%SZ")),
            last_attempt_at=time.mktime(time.strptime(existing_state.last_attempt_at, "%Y-%m-%dT%H:%M:%SZ")),
        )
    else:
        # Create new state
        state = create_state(repository=repo_path, branch=branch, remote=remote)
        save_state(state)
        retry_state = RetryState(
            attempt=0,
            last_error=None,
            started_at=time.time(),
        )

    # Create retry engine
    retry_engine = RetryEngine(
        initial_delay_seconds=config.retry.initial_delay_seconds,
        max_backoff_seconds=config.retry.max_backoff_seconds,
        linear=config.retry.linear,
    )

    # Track state updates
    def on_retry(retry_state: RetryState) -> None:
        """Update state file on each retry."""
        state = OperationState(
            operation_id=operation_id,
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(retry_state.started_at)),
            attempts=retry_state.attempt,
            last_attempt_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(retry_state.last_attempt_at)),
            last_error=retry_state.last_error,
            repository=repo_path,
            branch=branch,
            remote=remote,
        )
        save_state(state)

        # Log retry attempt
        backoff = retry_engine.calculate_backoff(retry_state.attempt)
        logger.info(
            "Push attempt failed",
            attempt=retry_state.attempt,
            backoff=backoff,
            error=retry_state.last_error,
        )

        # Follow mode: tail log file
        if args.follow:
            from git_submit.log_handler import LOG_DIR
            log_file = LOG_DIR / f"{operation_id}.log"
            entries = tail_log(log_file, lines=5)
            for entry in entries:
                print(str(entry))

    # Handle force flag
    if args.force:
        print("\n⚠ WARNING: --force flag enabled. This may rewrite remote history.")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() not in ("yes", "y"):
            print("Aborted.")
            return 1

    # Execute with retry
    try:
        import time
        start_time = time.time()

        result = asyncio.run(
            retry_engine.execute_with_retry(
                remote=remote,
                branch=branch,
                all_branches=args.all,
                force=args.force,
                dry_run=args.dry_run,
                on_retry=on_retry,
            )
        )

        duration = time.time() - start_time

        if result.success:
            logger.info(
                "Push successful",
                attempts=retry_state.attempt,
                duration=duration,
            )

            if not args.quiet:
                print(f"\n✓ Push successful after {retry_state.attempt} attempt(s)!")
                print(f"  Duration: {duration:.1f}s")

            # Send notifications
            send_notifications(
                config=config,
                repo=repo_path,
                branch=branch,
                commit_sha=result.stdout.split()[-1][:8] if result.stdout else "unknown",
                attempts=retry_state.attempt,
                duration=duration,
            )

            # Clean up state
            delete_state(operation_id)

            return 0
        else:
            logger.error("Push failed", error=result.stderr)
            return 1

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        return 1


def send_notifications(config, repo: str, branch: str, commit_sha: str, attempts: int, duration: float) -> None:
    """Send all enabled notifications."""
    from git_submit.notifications import EmailNotifier, DesktopNotifier, WebhookNotifier

    # Email
    if config.notifications.email.enabled:
        email = EmailNotifier(
            enabled=config.notifications.email.enabled,
            smtp_host=config.notifications.email.smtp_host,
            smtp_port=config.notifications.email.smtp_port,
            username=config.notifications.email.username,
            password_env=config.notifications.email.password_env,
            from_address=config.notifications.email.from_address,
            to_address=config.notifications.email.to_address,
        )
        email.send(repo=repo, branch=branch, commit_sha=commit_sha, attempts=attempts, duration=duration)

    # Desktop
    if config.notifications.desktop.enabled:
        desktop = DesktopNotifier(enabled=config.notifications.desktop.enabled)
        desktop.send(repo=repo, branch=branch)

    # Webhooks
    if config.notifications.webhooks:
        webhook = WebhookNotifier(
            webhooks=[
                {"url": w.url, "headers": w.headers}
                for w in config.notifications.webhooks
            ]
        )
        asyncio.run(
            webhook.send(repo=repo, branch=branch, commit_sha=commit_sha, attempts=attempts, duration=duration)
        )


def cmd_status(args) -> int:
    """Show operation status."""
    from git_submit.status_commands import cmd_status as status_cmd
    return status_cmd(orphaned=args.orphaned)


def cmd_cleanup(args) -> int:
    """Remove orphaned state files."""
    from git_submit.status_commands import cmd_cleanup as cleanup_cmd
    return cleanup_cmd()


def cmd_history(args) -> int:
    """Show recent operations."""
    from git_submit.status_commands import cmd_history as history_cmd
    return history_cmd()


def cmd_help_examples(args) -> int:
    """Show usage examples."""
    print("""
git-submit Usage Examples
======================

Basic usage:
  git-submit push                      # Push current branch with auto-retry
  git-submit push --remote origin --branch main
  git-submit push --all                # Push all branches

Enable notifications:
  git-submit push --notify-desktop
  git-submit push --notify-email
  git-submit push --notify-webhook https://hooks.slack.com/...

Configuration:
  git-submit config init                  # Create config file
  git-submit config edit                  # Open config in editor
  git-submit config show                  # Show effective config
  git-submit config validate               # Validate config

Status and cleanup:
  git-submit status                       # Show active operations
  git-submit status --orphaned            # List old state files
  git-submit cleanup                      # Remove orphaned states
  git-submit history                      # Show recent operations

Logging options:
  git-submit push --verbose               # Show detailed progress
  git-submit push --quiet                 # Suppress stdout
  git-submit push --json                  # JSON output
  git-submit push --follow                # Tail log file

Testing:
  git-submit push --dry-run              # Validate without pushing
""")
    return 0


def main() -> int:
    """Main entry point."""
    # Parse args
    args = parse_args()

    # Load config
    try:
        config = load_config()
    except ConfigLoadError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("Run 'git-submit config init' to create a configuration file.", file=sys.stderr)
        return 1

    # Merge CLI args with config
    try:
        config = merge_args_with_config(args, config)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    # Dispatch command
    if not args.command or args.command == "help":
        if hasattr(args, 'topic') and args.topic == "examples":
            return cmd_help_examples(args)
        else:
            # Show help - recreate parser and display it
            import argparse
            parser = argparse.ArgumentParser(
                prog="git-submit",
                description="Automated git push with infinite retry logic and notifications",
                formatter_class=argparse.RawDescriptionHelpFormatter,
            )
            subparsers = parser.add_subparsers(dest="command", help="Available commands")

            # Push command
            push_parser = subparsers.add_parser("push", help="Push to git with automatic retries")
            git_group = push_parser.add_argument_group("Git Options")
            git_group.add_argument("--remote", help="Remote to push to")
            git_group.add_argument("--branch", help="Branch to push")
            git_group.add_argument("--all", action="store_true", help="Push all branches")
            git_group.add_argument("--force", "-f", action="store_true", help="Force push")
            git_group.add_argument("--dry-run", action="store_true", help="Validate without pushing")

            retry_group = push_parser.add_argument_group("Retry Options")
            retry_group.add_argument("--max-retries", type=int, help="Maximum retry attempts (0=infinite)")
            retry_group.add_argument("--initial-delay", type=int, help="Initial retry delay in seconds")
            retry_group.add_argument("--max-backoff", type=int, help="Maximum backoff time in seconds")
            retry_group.add_argument("--linear", action="store_true", help="Use linear backoff")

            notify_group = push_parser.add_argument_group("Notification Options")
            notify_group.add_argument("--notify-desktop", action="store_true", help="Enable desktop notifications")
            notify_group.add_argument("--notify-email", action="store_true", help="Enable email notifications")
            notify_group.add_argument("--notify-webhook", action="store_true", help="Enable webhook notifications")

            output_group = push_parser.add_argument_group("Output Options")
            output_group.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
            output_group.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
            output_group.add_argument("--follow", "-f", action="store_true", help="Follow log output")

            # Config command
            config_parser = subparsers.add_parser("config", help="Configuration management")
            config_subparsers = config_parser.add_subparsers(dest="config_command")
            config_subparsers.add_parser("init", help="Initialize configuration")
            config_subparsers.add_parser("edit", help="Edit configuration")
            config_subparsers.add_parser("validate", help="Validate configuration")
            config_subparsers.add_parser("show", help="Show configuration")

            # Status command
            status_parser = subparsers.add_parser("status", help="Show operation status")
            status_parser.add_argument("--orphaned", action="store_true", help="Show orphaned operations")

            # Cleanup command
            subparsers.add_parser("cleanup", help="Remove orphaned state files")

            # History command
            subparsers.add_parser("history", help="Show operation history")

            # Help command
            help_parser = subparsers.add_parser("help", help="Show help")
            help_parser.add_argument("--topic", choices=["examples"], help="Help topic")

            parser.print_help()
            return 0

    if args.command == "config":
        if args.config_command == "init":
            return config_init()
        elif args.config_command == "edit":
            return config_edit()
        elif args.config_command == "validate":
            return config_validate()
        elif args.config_command == "show":
            return config_show()
        else:
            return config_init()  # Default to init

    if args.command == "push":
        return cmd_push(args, config)

    if args.command == "status":
        return cmd_status(args)

    if args.command == "cleanup":
        return cmd_cleanup(args)

    if args.command == "history":
        return cmd_history(args)

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
