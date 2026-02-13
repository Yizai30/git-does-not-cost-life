"""Configuration file loader with YAML support."""

import os
from pathlib import Path

import yaml
from pydantic import ValidationError

from git_submit.config import AppConfig


class ConfigLoadError(Exception):
    """Raised when configuration cannot be loaded."""

    pass


class ConfigValidationError(ConfigLoadError):
    """Raised when configuration fails validation."""

    pass


DEFAULT_CONFIG_PATH = Path.home() / ".git-submit" / "config.yaml"


def load_config(config_path: Path | None = None) -> AppConfig:
    """
    Load configuration from YAML file with fallback to defaults.

    Args:
        config_path: Path to config file. If None, uses default ~/.git-submit/config.yaml

    Returns:
        AppConfig instance

    Raises:
        ConfigLoadError: If config file exists but cannot be read
        ConfigValidationError: If config file fails validation
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    if not config_path.exists():
        # Return default configuration
        return AppConfig()

    try:
        with open(config_path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigLoadError(f"Failed to parse config file: {e}")
    except OSError as e:
        raise ConfigLoadError(f"Failed to read config file: {e}")

    try:
        return AppConfig(**config_data)
    except ValidationError as e:
        raise ConfigValidationError(f"Configuration validation failed:\n{e}")


def save_config(config: AppConfig, config_path: Path | None = None) -> None:
    """
    Save configuration to YAML file.

    Args:
        config: AppConfig instance to save
        config_path: Path to config file. If None, uses default ~/.git-submit/config.yaml

    Raises:
        ConfigLoadError: If config file cannot be written
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_dict = config.model_dump()

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    except OSError as e:
        raise ConfigLoadError(f"Failed to write config file: {e}")


def get_default_config() -> str:
    """
    Get default configuration as YAML string.

    Returns:
        YAML string with default configuration and comments
    """
    return """# git-submit configuration file
# Location: ~/.git-submit/config.yaml

# Retry settings
retry:
  # Initial delay before first retry (seconds)
  initial_delay_seconds: 5
  # Maximum backoff interval (seconds)
  max_backoff_seconds: 300
  # Use linear retry instead of exponential backoff
  linear: false

# Git settings
git:
  # Default remote to push to
  remote: origin
  # Branch to push (use 'auto' to detect current branch)
  branch: auto

# Notification settings
notifications:
  # Desktop notifications (Windows Toast, macOS NotificationCenter, Linux freedesktop)
  desktop:
    enabled: true

  # Email notifications via SMTP
  email:
    enabled: false
    # SMTP server configuration
    smtp_host: smtp.example.com
    smtp_port: 587
    username: your-email@example.com
    # Reference to environment variable containing password
    password_env: SMTP_PASSWORD
    from_address: git-submit@example.com
    to_address: your-email@example.com

  # Webhook notifications (HTTP POST)
  webhooks:
    - url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      headers:
        Authorization: "Bearer YOUR_TOKEN"
"""
