"""Main CLI interface for git-submit."""

import asyncio
import os
import sys
from pathlib import Path

from git_submit.cli_args import parse_args, merge_args_with_config
from git_submit.config_loader import load_config, ConfigLoadError
from git_submit.config_commands import (
    cmd_init as config_init,
    cmd_edit as config_edit,
    cmd_validate as config_validate,
    cmd_show as config_show,
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
from git_submit.logging import Logger, LogLevel, tail_log


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
        retry_state = existing_state
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
            from git_submit.logging import LOG_DIR
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
    if args.orphaned:
        # List orphaned state files
        states = [load_state(path.stem) for path in list_state_files()]
        orphaned = [s for s in states if s and is_orphaned(s)]

        if not orphaned:
            print("No orphaned state files found.")
            return 0

        print(f"Orphaned state files ({len(orphaned)}):")
        for state in orphaned:
            age = (datetime.now() - datetime.fromisoformat(state.started_at)).days
            print(f"  - {state.operation_id}: {state.repository}/{state.branch} ({age} days old)")
        return 0
    else:
        # Show active operation
        states = [load_state(path.stem) for path in list_state_files()]
        active = [s for s in states if s]

        if not active:
            print("No active operations found.")
            return 0

        print(f"Active operations ({len(active)}):")
        for state in active:
            print(f"  - {state.operation_id}:")
            print(f"      Repository: {state.repository}")
            print(f"      Branch: {state.branch}")
            print(f"      Attempts: {state.attempts}")
            print(f"      Started: {state.started_at}")
            if state.last_error:
                print(f"      Last error: {state.last_error[:80]}...")

        return 0


def cmd_cleanup(args) -> int:
    """Remove orphaned state files."""
    from datetime import datetime

    states = [load_state(path.stem) for path in list_state_files()]
    orphaned = [s for s in states if s and is_orphaned(s)]

    if not orphaned:
        print("No orphaned state files to clean up.")
        return 0

    from git_submit.state_manager import delete_state
    for state in orphaned:
        delete_state(state.operation_id)

    print(f"Removed {len(orphaned)} orphaned state file(s).")
    return 0


def cmd_history(args) -> int:
    """Show recent operations."""
    from git_submit.logging import tail_log, LOG_DIR

    # Get all log files
    log_files = list(LOG_DIR.glob("*.log"))

    if not log_files:
        print("No operation history found.")
        return 0

    # Sort by modification time
    log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Show last 10 operations
    print("Recent operations (last 10):")
    for log_file in log_files[:10]:
        entries = tail_log(log_file, lines=1)
        if entries:
            entry = entries[0]
            timestamp = entry.data.get("timestamp", "")
            event = entry.data.get("event", "")
            print(f"  - [{timestamp}] {event}")

    return 0


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
        if args.topic == "examples":
            return cmd_help_examples(args)
        else:
            from git_submit.cli_args import parse_args
            parse_args(["--help"])
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
