"""Unit tests for configuration loading and validation."""

import pytest
import os
from pathlib import Path

from git_submit.config import AppConfig, RetryConfig, GitConfig
from git_submit.config_loader import load_config, save_config, get_default_config
from git_submit.config_loader import ConfigLoadError, ConfigValidationError


def test_default_config():
    """Test default configuration values."""
    config = AppConfig()

    assert config.retry.initial_delay_seconds == 5
    assert config.retry.max_backoff_seconds == 300
    assert config.retry.linear is False
    assert config.git.remote == "origin"
    assert config.git.branch == "auto"
    assert config.notifications.desktop.enabled is True
    assert config.notifications.email.enabled is False


def test_load_config_missing_file():
    """Test loading config when file doesn't exist returns defaults."""
    # Non-existent path
    config = load_config(Path("/non/existent/path.yaml"))

    assert isinstance(config, AppConfig)
    assert config.retry.initial_delay_seconds == 5


def test_config_retry_validation():
    """Test retry config validation."""
    # Valid config
    config = RetryConfig(initial_delay_seconds=10, max_backoff_seconds=600, linear=True)
    assert config.initial_delay_seconds == 10

    # Invalid: negative delay
    with pytest.raises(ValueError):
        RetryConfig(initial_delay_seconds=-1)

    # Invalid: delay exceeds max
    with pytest.raises(ValueError):
        RetryConfig(initial_delay_seconds=10000)


def test_config_email_validation():
    """Test email config validation including password_env."""
    from git_submit.config import EmailConfig

    # Valid: password_env exists
    os.environ["TEST_PASSWORD"] = "secret"
    config = EmailConfig(
        enabled=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="user@example.com",
        password_env="TEST_PASSWORD",
        from_address="from@example.com",
        to_address="to@example.com",
    )
    assert config.password_env == "TEST_PASSWORD"

    # Invalid: password_env doesn't exist
    with pytest.raises(ValueError, match="Environment variable.*not found"):
        EmailConfig(
            enabled=True,
            smtp_host="smtp.example.com",
            password_env="NONEXISTENT_VAR",
        )


def test_save_config():
    """Test saving configuration to file."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test-config.yaml"

        config = AppConfig()
        save_config(config, config_path)

        assert config_path.exists()

        # Load and verify
        loaded = load_config(config_path)
        assert loaded.retry.initial_delay_seconds == config.retry.initial_delay_seconds


def test_get_default_config():
    """Test default config template generation."""
    default_config = get_default_config()

    assert "# git-submit configuration file" in default_config
    assert "retry:" in default_config
    assert "notifications:" in default_config
    assert "desktop:" in default_config
