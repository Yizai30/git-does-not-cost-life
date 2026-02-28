"""Notification modules for email, desktop, and webhook."""

import os
import smtplib
import asyncio
from datetime import datetime
from email.message import EmailMessage
from typing import List
import httpx


class EmailNotifier:
    """Email notification via SMTP."""

    def __init__(
        self,
        enabled: bool,
        smtp_host: str | None,
        smtp_port: int,
        username: str | None,
        password_env: str | None,
        from_address: str | None,
        to_address: str | None,
    ):
        """
        Initialize email notifier.

        Args:
            enabled: Whether email notifications are enabled
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password_env: Environment variable name containing password
            from_address: From email address
            to_address: To email address
        """
        self.enabled = enabled
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password_env = password_env
        self.from_address = from_address
        self.to_address = to_address

    def validate(self) -> List[str]:
        """
        Validate email configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if self.enabled:
            if not self.smtp_host:
                errors.append("SMTP host not configured")
            if not self.username:
                errors.append("SMTP username not configured")
            if not self.password_env:
                errors.append("Password environment variable not configured")
            if not self.from_address:
                errors.append("From address not configured")
            if not self.to_address:
                errors.append("To address not configured")

        return errors

    def send(
        self,
        repo: str,
        branch: str,
        commit_sha: str,
        attempts: int,
        duration: float,
    ) -> bool:
        """
        Send email notification.

        Args:
            repo: Repository name/path
            branch: Branch name
            commit_sha: Commit SHA that was pushed
            attempts: Number of retry attempts
            duration: Total duration in seconds

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        # Get password from environment
        password = os.environ.get(self.password_env, "") if self.password_env else None

        try:
            # Create message
            msg = EmailMessage()
            msg["Subject"] = f"✓ GitHub Push Successful: {repo}/{branch}"
            msg["From"] = self.from_address
            msg["To"] = self.to_address

            body = self._render_template(repo, branch, commit_sha, attempts, duration)
            msg.set_content(body)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()  # Enable TLS
                server.login(self.username, password)
                server.send_message(msg)

            return True

        except Exception as e:
            # Log but don't fail the operation
            print(f"⚠ Email notification failed: {e}", file=sys.stderr)
            return False

    def _render_template(
        self, repo: str, branch: str, commit_sha: str, attempts: int, duration: float
    ) -> str:
        """Render email body template."""
        return f"""GitHub push completed successfully!

Repository: {repo}
Branch: {branch}
Commit: {commit_sha}
Attempts: {attempts}
Duration: {duration:.1f} seconds

Timestamp: {datetime.now().isoformat()}
"""


class DesktopNotifier:
    """Desktop notification using plyer."""

    def __init__(self, enabled: bool):
        """
        Initialize desktop notifier.

        Args:
            enabled: Whether desktop notifications are enabled
        """
        self.enabled = enabled
        self._plyer = None
        if enabled:
            try:
                from plyer import notification
                self._plyer = notification
            except ImportError:
                print("⚠ Desktop notifications unavailable (plyer not installed)", file=sys.stderr)
            except Exception as e:
                print(f"⚠ Desktop notifications unavailable: {e}", file=sys.stderr)

    def send(self, repo: str, branch: str) -> bool:
        """
        Send desktop notification.

        Args:
            repo: Repository name
            branch: Branch name

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled or not self._plyer:
            return False

        try:
            self._plyer.notify(
                title="GitHub Push Successful",
                message=f"{repo}/{branch}",
                app_name="git-submit",
                timeout=10,
            )
            return True
        except Exception as e:
            print(f"⚠ Desktop notification failed: {e}", file=sys.stderr)
            return False


class WebhookNotifier:
    """Webhook notification via HTTP POST."""

    def __init__(self, webhooks: List[dict]):
        """
        Initialize webhook notifier.

        Args:
            webhooks: List of webhook configs with 'url' and optional 'headers'
        """
        self.webhooks = webhooks

    async def send(
        self,
        repo: str,
        branch: str,
        commit_sha: str,
        attempts: int,
        duration: float,
    ) -> None:
        """
        Send webhook notifications to all configured URLs.

        Args:
            repo: Repository name
            branch: Branch name
            commit_sha: Commit SHA
            attempts: Retry attempts
            duration: Total duration
        """
        if not self.webhooks:
            return

        # Prepare payload
        payload = {
            "status": "success",
            "repository": repo,
            "branch": branch,
            "commit_sha": commit_sha,
            "attempts": attempts,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

        # Send to all webhooks concurrently
        async with httpx.AsyncClient(timeout=10.0) as client:
            tasks = []
            for webhook in self.webhooks:
                task = self._send_webhook(client, webhook, payload)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    url = self.webhooks[i]["url"]
                    print(f"⚠ Webhook failed ({url}): {result}", file=sys.stderr)

    async def _send_webhook(
        self, client: httpx.Client, webhook: dict, payload: dict
    ) -> None:
        """Send webhook to single URL."""
        url = webhook["url"]
        headers = webhook.get("headers", {})

        response = await client.post(url, json=payload, headers=headers)

        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}")


# Import sys here to avoid circular dependency
import sys
