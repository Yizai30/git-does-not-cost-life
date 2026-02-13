"""Structured JSON logging system."""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


LOG_DIR = Path.home() / ".git-submit" / "logs"


class LogEntry:
    """Structured log entry."""

    def __init__(
        self,
        level: LogLevel,
        event: str,
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        attempt: Optional[int] = None,
        error: Optional[str] = None,
        **extra_fields,
    ):
        """
        Create log entry.

        Args:
            level: Log level
            event: Event description
            repository: Repository path
            branch: Branch name
            attempt: Retry attempt number
            error: Error message
            **extra_fields: Additional fields for log entry
        """
        self.data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.value,
            "event": event,
        }

        # Add optional fields
        if repository is not None:
            self.data["repository"] = repository
        if branch is not None:
            self.data["branch"] = branch
        if attempt is not None:
            self.data["attempt"] = attempt
        if error is not None:
            self.data["error"] = error

        # Add extra fields
        self.data.update(extra_fields)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.data)

    def __str__(self) -> str:
        """Human-readable format."""
        parts = [f"[{self.data['level']}]", self.data['event']]

        if "attempt" in self.data:
            parts.append(f"(attempt {self.data['attempt']})")
        if "backoff" in self.data:
            parts.append(f"next retry in {self.data['backoff']:.1f}s")
        if "duration" in self.data:
            parts.append(f"duration: {self.data['duration']:.1f}s")
        if "error" in self.data:
            parts.append(f"- {self.data['error']}")

        return " ".join(parts)


class Logger:
    """Structured logger with file and optional stdout output."""

    def __init__(
        self,
        operation_id: str,
        log_file: Optional[Path] = None,
        verbose: bool = False,
        quiet: bool = False,
        json_output: bool = False,
    ):
        """
        Initialize logger.

        Args:
            operation_id: Operation identifier for log file naming
            log_file: Custom log file path (auto-generated if None)
            verbose: Print to stdout in human-readable format
            quiet: Suppress all stdout output
            json_output: Print raw JSON to stdout
        """
        self.operation_id = operation_id
        self.verbose = verbose
        self.quiet = quiet
        self.json_output = json_output

        # Generate log file path if not provided
        if log_file is None:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            # Daily rotation: include date in filename
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = LOG_DIR / f"{operation_id}-{date_str}.log"

        self.log_file = log_file

    def log(self, entry: LogEntry) -> None:
        """
        Write log entry to file and optionally stdout.

        Args:
            entry: LogEntry to write
        """
        # Write to file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry.to_json() + "\n")
        except OSError:
            pass  # Fail silently if log write fails

        # Write to stdout if not quiet
        if not self.quiet:
            if self.json_output:
                print(entry.to_json())
            elif self.verbose or entry.data["level"] in (LogLevel.WARNING.value, LogLevel.ERROR.value):
                print(str(entry))

    def debug(self, event: str, **fields) -> None:
        """Log DEBUG message."""
        self.log(LogEntry(LogLevel.DEBUG, event, **fields))

    def info(self, event: str, **fields) -> None:
        """Log INFO message."""
        self.log(LogEntry(LogLevel.INFO, event, **fields))

    def warning(self, event: str, **fields) -> None:
        """Log WARNING message."""
        self.log(LogEntry(LogLevel.WARNING, event, **fields))

    def error(self, event: str, **fields) -> None:
        """Log ERROR message."""
        self.log(LogEntry(LogLevel.ERROR, event, **fields))


def tail_log(log_file: Path, lines: int = 20) -> list[LogEntry]:
    """
    Tail log file and return recent entries.

    Args:
        log_file: Log file path
        lines: Number of lines to return

    Returns:
        List of recent LogEntry objects
    """
    if not log_file.exists():
        return []

    entries = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # Read last N lines
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                try:
                    data = json.loads(line.strip())
                    # Reconstruct LogEntry
                    entry = LogEntry(
                        level=LogLevel(data["level"]),
                        event=data["event"],
                    )
                    entry.data = data
                    entries.append(entry)
                except (json.JSONDecodeError, KeyError):
                    continue
    except OSError:
        pass

    return entries
