"""Configuration models using Pydantic for validation."""

import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RetryConfig(BaseModel):
    """Retry configuration settings."""

    initial_delay_seconds: int = Field(default=5, ge=1, le=3600)
    max_backoff_seconds: int = Field(default=300, ge=1, le=86400)
    linear: bool = Field(default=False)


class GitConfig(BaseModel):
    """Git configuration settings."""

    remote: str = Field(default="origin")
    branch: str = Field(default="auto")


class EmailConfig(BaseModel):
    """Email notification configuration."""

    enabled: bool = Field(default=False)
    smtp_host: Optional[str] = Field(default=None)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    username: Optional[str] = Field(default=None)
    password_env: Optional[str] = Field(default=None)
    from_address: Optional[str] = Field(default=None)
    to_address: Optional[str] = Field(default=None)

    @field_validator("password_env")
    @classmethod
    def validate_password_env(cls, v: Optional[str]) -> Optional[str]:
        """Validate that password_env references an existing environment variable."""
        if v and v not in os.environ:
            raise ValueError(
                f"Environment variable '{v}' referenced in password_env not found"
            )
        return v


class DesktopConfig(BaseModel):
    """Desktop notification configuration."""

    enabled: bool = Field(default=True)


class WebhookConfig(BaseModel):
    """Webhook notification configuration."""

    url: str
    headers: dict[str, str] = Field(default_factory=dict)


class NotificationConfig(BaseModel):
    """Notification settings."""

    email: EmailConfig = Field(default_factory=EmailConfig)
    desktop: DesktopConfig = Field(default_factory=DesktopConfig)
    webhooks: list[WebhookConfig] = Field(default_factory=list)


class AppConfig(BaseModel):
    """Main application configuration."""

    retry: RetryConfig = Field(default_factory=RetryConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
