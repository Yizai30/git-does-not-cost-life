#!/usr/bin/env python3
"""Simple config init script without type hints."""

import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def config_init():
    """Initialize config file."""
    DEFAULT_CONFIG_PATH = Path.home() / ".git-submit" / "config.yaml"

    if DEFAULT_CONFIG_PATH.exists():
        print(f"Configuration file already exists: {DEFAULT_CONFIG_PATH}")
        print("Edit with: git-submit config edit")
        return 1

    DEFAULT_CONFIG = """# git-submit configuration file
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

    DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(DEFAULT_CONFIG_PATH, 'w', encoding='utf-8') as f:
        f.write(DEFAULT_CONFIG)

    print(f"Created configuration file: {DEFAULT_CONFIG_PATH}")
    print("Edit with: git-submit config edit")
    return 0

if __name__ == "__main__":
    sys.exit(config_init())
