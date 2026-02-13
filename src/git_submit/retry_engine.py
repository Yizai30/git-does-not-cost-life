"""Retry engine with exponential backoff and jitter."""

import asyncio
import random
import time
from dataclasses import dataclass

from git_submit.git_wrapper import (
    GitResult,
    push,
    verify_push,
    PERMANENT_ERROR_PATTERNS,
)


@dataclass
class RetryState:
    """State tracking for retry operations."""

    attempt: int = 0
    last_error: str | None = None
    started_at: float = 0.0  # Unix timestamp
    last_attempt_at: float = 0.0


class RetryEngine:
    """Manages retry logic with exponential backoff and jitter."""

    def __init__(
        self,
        initial_delay_seconds: int = 5,
        max_backoff_seconds: int = 300,
        linear: bool = False,
    ):
        """
        Initialize retry engine.

        Args:
            initial_delay_seconds: Initial delay before first retry
            max_backoff_seconds: Maximum backoff cap
            linear: If True, use constant delay instead of exponential
        """
        self.initial_delay = initial_delay_seconds
        self.max_backoff = max_backoff_seconds
        self.linear = linear
        self.state = RetryState()

    def calculate_backoff(self, attempt: int) -> float:
        """
        Calculate backoff delay with exponential backoff and jitter.

        Formula: delay = min(max_backoff, (initial_delay * 2^(attempt-1))) * random(0.75, 1.25)

        Args:
            attempt: Retry attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        if self.linear:
            # Linear: constant delay with jitter
            base_delay = self.initial_delay
        else:
            # Exponential: double each attempt
            base_delay = self.initial_delay * (2 ** (attempt - 1))

        # Cap at maximum
        base_delay = min(base_delay, self.max_backoff)

        # Add jitter (±25%)
        jitter = random.uniform(0.75, 1.25)

        return base_delay * jitter

    def is_permanent_error(self, error_output: str) -> bool:
        """
        Detect if error is permanent (repo not found, etc.).

        Args:
            error_output: stderr or error message from git push

        Returns:
            True if error appears permanent
        """
        error_lower = error_output.lower()
        for pattern in PERMANENT_ERROR_PATTERNS:
            if pattern in error_lower:
                return True
        return False

    async def execute_with_retry(
        self,
        remote: str,
        branch: str,
        all_branches: bool = False,
        force: bool = False,
        dry_run: bool = False,
        on_retry: callable[[RetryState], None] | None = None,
    ) -> GitResult:
        """
        Execute git push with infinite retry until success.

        Args:
            remote: Git remote name
            branch: Branch to push
            all_branches: Push all branches
            force: Force push
            dry_run: Validate without pushing
            on_retry: Callback for each retry attempt

        Returns:
            GitResult of successful push

        Raises:
            KeyboardInterrupt: If user cancels
        """
        import time

        self.state.started_at = time.time()

        while True:
            self.state.attempt += 1
            self.state.last_attempt_at = time.time()

            try:
                result = push(
                    remote=remote,
                    branch=branch,
                    all_branches=all_branches,
                    force=force,
                    dry_run=dry_run,
                )

                if result.success:
                    # Optional verification
                    if not all_branches and verify_push(remote, branch):
                        return result
                    elif all_branches:
                        return result

                # Check for permanent errors
                if self.is_permanent_error(result.stderr):
                    # Log warning but continue retrying
                    # (user might fix repo while tool is running)
                    import sys
                    print(
                        f"\n⚠ WARNING: Detected possible permanent error:\n  {result.stderr}\n"
                        f"This may require manual intervention, but will continue retrying.\n"
                        f"Press Ctrl+C to stop.\n",
                        file=sys.stderr,
                    )

                # Calculate backoff
                if self.state.attempt > 1:
                    delay = self.calculate_backoff(self.state.attempt - 1)
                    self.state.last_error = result.stderr.strip() or result.stdout.strip()

                    if on_retry:
                        on_retry(self.state)

                    print(f"\nRetry {self.state.attempt} failed, waiting {delay:.1f}s...")
                    time.sleep(delay)

            except KeyboardInterrupt:
                print("\n\nRetry cancelled by user.")
                raise

            except Exception as e:
                # Unexpected error - log and retry
                self.state.last_error = str(e)
                if on_retry:
                    on_retry(self.state)

                delay = self.calculate_backoff(self.state.attempt)
                print(f"\nUnexpected error: {e}\nRetrying in {delay:.1f}s...")
                time.sleep(delay)
