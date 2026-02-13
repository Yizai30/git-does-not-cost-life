"""Configuration management commands."""

import os
import subprocess
import sys

from git_submit.config_loader import (
    load_config,
    save_config,
    get_default_config,
    ConfigLoadError,
    ConfigValidationError,
)


def cmd_init() -> int:
    """Initialize configuration file with defaults."""
    from git_submit.config_loader import DEFAULT_CONFIG_PATH

    if DEFAULT_CONFIG_PATH.exists():
        print(f"Configuration file already exists: {DEFAULT_CONFIG_PATH}")
        print("Edit with: git-submit config edit")
        return 1

    try:
        default_config = get_default_config()
        DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEFAULT_CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(default_config)
        print(f"Created configuration file: {DEFAULT_CONFIG_PATH}")
        print("Edit with: git-submit config edit")
        return 0
    except OSError as e:
        print(f"Error creating config file: {e}", file=sys.stderr)
        return 1


def cmd_edit() -> int:
    """Open configuration file in default editor."""
    from git_submit.config_loader import DEFAULT_CONFIG_PATH

    if not DEFAULT_CONFIG_PATH.exists():
        print(f"Configuration file not found: {DEFAULT_CONFIG_PATH}")
        print("Create with: git-submit config init")
        return 1

    # Try common editors
    editor = os.environ.get("GIT_EDITOR") or os.environ.get("EDITOR") or None

    if editor:
        try:
            subprocess.run([editor, str(DEFAULT_CONFIG_PATH)])
            return 0
        except Exception as e:
            print(f"Error launching editor: {e}", file=sys.stderr)
            return 1
    else:
        # Open with default system editor
        import platform

        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(str(DEFAULT_CONFIG_PATH))  # type: ignore[attr-defined]
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(DEFAULT_CONFIG_PATH)])
            else:  # Linux
                subprocess.run(["xdg-open", str(DEFAULT_CONFIG_PATH)])
            return 0
        except Exception as e:
            print(f"Error opening config file: {e}", file=sys.stderr)
            return 1


def cmd_validate() -> int:
    """Validate configuration file."""
    from git_submit.config_loader import DEFAULT_CONFIG_PATH

    if not DEFAULT_CONFIG_PATH.exists():
        print(f"Configuration file not found: {DEFAULT_CONFIG_PATH}")
        print("Create with: git-submit config init")
        return 1

    try:
        config = load_config()
        print("✓ Configuration is valid")
        print(f"  Retry: {config.retry.initial_delay_seconds}s initial, "
              f"{config.retry.max_backoff_seconds}s max")
        print(f"  Git remote: {config.git.remote}, branch: {config.git.branch}")
        print(f"  Desktop notifications: {'enabled' if config.notifications.desktop.enabled else 'disabled'}")
        print(f"  Email notifications: {'enabled' if config.notifications.email.enabled else 'disabled'}")
        print(f"  Webhooks: {len(config.notifications.webhooks)} configured")
        return 0
    except ConfigValidationError as e:
        print(f"✗ Configuration validation failed:\n{e}", file=sys.stderr)
        return 1
    except ConfigLoadError as e:
        print(f"✗ Error loading configuration:\n{e}", file=sys.stderr)
        return 1


def cmd_show() -> int:
    """Show effective configuration."""
    try:
        config = load_config()
        print("Effective Configuration:")
        print("=" * 50)
        print(f"Retry Settings:")
        print(f"  Initial delay: {config.retry.initial_delay_seconds}s")
        print(f"  Max backoff: {config.retry.max_backoff_seconds}s")
        print(f"  Linear retry: {config.retry.linear}")
        print()
        print(f"Git Settings:")
        print(f"  Remote: {config.git.remote}")
        print(f"  Branch: {config.git.branch}")
        print()
        print("Notification Settings:")
        print(f"  Desktop: {config.notifications.desktop.enabled}")
        if config.notifications.email.enabled:
            print(f"  Email:")
            print(f"    Host: {config.notifications.email.smtp_host}")
            print(f"    Port: {config.notifications.email.smtp_port}")
            print(f"    From: {config.notifications.email.from_address}")
            print(f"    To: {config.notifications.email.to_address}")
        if config.notifications.webhooks:
            print(f"  Webhooks ({len(config.notifications.webhooks)}):")
            for i, webhook in enumerate(config.notifications.webhooks, 1):
                print(f"    {i}. {webhook.url}")
        return 0
    except (ConfigLoadError, ConfigValidationError) as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        return 1
