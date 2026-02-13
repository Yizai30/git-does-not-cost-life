"""CLI argument parser with precedence: CLI flags > config file > defaults."""

import argparse
from pathlib import Path

from git_submit.config import (
    AppConfig,
    RetryConfig,
    GitConfig,
    NotificationConfig,
    DesktopConfig,
    EmailConfig,
)


def parse_args(config: AppConfig | None = None) -> argparse.Namespace:
    """
    Parse CLI arguments with precedence over config file.

    Args:
        config: Loaded configuration (if available)

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="git-submit",
        description="Automated git push with infinite retry logic and notifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Push command
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    push_parser = subparsers.add_parser("push", help="Push to git with automatic retries")

    # Git options
    git_group = push_parser.add_argument_group("Git Options")
    git_group.add_argument(
        "--remote",
        help="Remote to push to (overrides config)",
    )
    git_group.add_argument(
        "--branch",
        help="Branch to push (overrides config, 'auto' to detect)",
    )
    git_group.add_argument(
        "--all",
        action="store_true",
        help="Push all branches (git push --all)",
    )

    # Retry options
    retry_group = push_parser.add_argument_group("Retry Options")
    retry_group.add_argument(
        "--retry-delay",
        type=int,
        dest="initial_delay_seconds",
        help="Initial retry delay in seconds",
    )
    retry_group.add_argument(
        "--max-backoff",
        type=int,
        dest="max_backoff_seconds",
        help="Maximum backoff interval in seconds",
    )
    retry_group.add_argument(
        "--linear-retry",
        action="store_true",
        dest="linear",
        help="Use linear retry instead of exponential backoff",
    )
    retry_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config without pushing",
    )

    # Notification options
    notify_group = push_parser.add_argument_group("Notification Options")
    notify_group.add_argument(
        "--notify-email",
        action="store_true",
        help="Enable email notifications",
    )
    notify_group.add_argument(
        "--notify-desktop",
        action="store_true",
        help="Enable desktop notifications",
    )
    notify_group.add_argument(
        "--notify-webhook",
        action="append",
        dest="webhook_urls",
        help="Add webhook URL (can be specified multiple times)",
    )
    notify_group.add_argument(
        "--no-notify",
        action="store_true",
        help="Disable all notifications",
    )

    # Logging options
    log_group = push_parser.add_argument_group("Logging Options")
    log_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed progress to stdout",
    )
    log_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all stdout output",
    )
    log_group.add_argument(
        "--json",
        action="store_true",
        help="Output logs as JSON",
    )
    log_group.add_argument(
        "--follow",
        action="store_true",
        help="Tail log file in real-time",
    )

    # Other options
    push_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force push (with confirmation prompt)",
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_command")

    config_init = config_subparsers.add_parser("init", help="Create default config file")
    config_edit = config_subparsers.add_parser("edit", help="Open config in editor")
    config_validate = config_subparsers.add_parser("validate", help="Validate configuration")
    config_show = config_subparsers.add_parser("show", help="Show effective configuration")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show operation status")
    status_parser.add_argument(
        "--orphaned",
        action="store_true",
        help="List orphaned state files",
    )

    # History command
    subparsers.add_parser("history", help="Show recent operations")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Remove orphaned state files")

    # Help command
    help_parser = subparsers.add_parser("help", help="Show help")
    help_parser.add_argument("topic", nargs="?", help="Help topic (e.g., 'examples')")

    args = parser.parse_args()

    return args


def merge_args_with_config(args: argparse.Namespace, config: AppConfig) -> AppConfig:
    """
    Merge CLI arguments with configuration (CLI takes precedence).

    Args:
        args: Parsed CLI arguments
        config: Loaded configuration

    Returns:
        Merged AppConfig
    """
    config_dict = config.model_dump()

    # Override with CLI flags if provided
    if hasattr(args, "remote") and args.remote:
        config_dict["git"]["remote"] = args.remote

    if hasattr(args, "branch") and args.branch:
        config_dict["git"]["branch"] = args.branch

    if hasattr(args, "initial_delay_seconds") and args.initial_delay_seconds:
        config_dict["retry"]["initial_delay_seconds"] = args.initial_delay_seconds

    if hasattr(args, "max_backoff_seconds") and args.max_backoff_seconds:
        config_dict["retry"]["max_backoff_seconds"] = args.max_backoff_seconds

    if hasattr(args, "linear") and args.linear:
        config_dict["retry"]["linear"] = True

    # Notification overrides
    if hasattr(args, "no_notify") and args.no_notify:
        config_dict["notifications"]["desktop"]["enabled"] = False
        config_dict["notifications"]["email"]["enabled"] = False
        config_dict["notifications"]["webhooks"] = []
    else:
        if hasattr(args, "notify_email") and args.notify_email:
            config_dict["notifications"]["email"]["enabled"] = True

        if hasattr(args, "notify_desktop") and args.notify_desktop:
            config_dict["notifications"]["desktop"]["enabled"] = True

        if hasattr(args, "webhook_urls") and args.webhook_urls:
            from git_submit.config import WebhookConfig
            config_dict["notifications"]["webhooks"] = [
                WebhookConfig(url=url) for url in args.webhook_urls
            ]

    try:
        return AppConfig(**config_dict)
    except ValidationError as e:
        raise ValueError(f"Configuration error: {e}")
