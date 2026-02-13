"""State persistence for crash safety and resume capability."""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
import time


@dataclass
class OperationState:
    """Persistent state for a retry operation."""

    operation_id: str
    started_at: str  # ISO 8601 timestamp
    attempts: int
    last_attempt_at: str  # ISO 8601 timestamp
    last_error: str | None
    repository: str
    branch: str
    remote: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "OperationState":
        """Create from dictionary."""
        return cls(**data)


STATE_DIR = Path.home() / ".git-submit" / "state"


def generate_operation_id(repository: str, branch: str) -> str:
    """
    Generate unique operation ID from repository path and branch.

    Args:
        repository: Repository path
        branch: Branch name

    Returns:
        Unique operation ID string
    """
    # Hash repository path to get consistent ID
    import hashlib
    repo_hash = hashlib.md5(repository.encode()).hexdigest()[:8]
    return f"{repo_hash}-{branch}".replace("/", "-").replace("\\", "-")


def get_state_path(operation_id: str) -> Path:
    """
    Get state file path for operation.

    Args:
        operation_id: Unique operation identifier

    Returns:
        Path to state file
    """
    return STATE_DIR / f"{operation_id}.json"


def create_state(
    repository: str,
    branch: str,
    remote: str,
) -> OperationState:
    """
    Create new operation state.

    Args:
        repository: Repository path
        branch: Branch name
        remote: Remote name

    Returns:
        New OperationState
    """
    operation_id = generate_operation_id(repository, branch)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return OperationState(
        operation_id=operation_id,
        started_at=now,
        attempts=0,
        last_attempt_at=now,
        last_error=None,
        repository=repository,
        branch=branch,
        remote=remote,
    )


def save_state(state: OperationState) -> None:
    """
    Save state to file atomically (crash safe).

    Args:
        state: OperationState to save

    Raises:
        OSError: If state file cannot be written
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path = get_state_path(state.operation_id)

    # Atomic write: temp file + rename
    temp_path = state_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2)

    # Atomic rename
    temp_path.replace(state_path)


def load_state(operation_id: str) -> Optional[OperationState]:
    """
    Load state from file.

    Args:
        operation_id: Operation identifier

    Returns:
        OperationState if exists, None otherwise
    """
    state_path = get_state_path(operation_id)

    if not state_path.exists():
        return None

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return OperationState.from_dict(data)
    except (json.JSONDecodeError, OSError):
        return None


def delete_state(operation_id: str) -> None:
    """
    Delete state file on successful completion.

    Args:
        operation_id: Operation identifier
    """
    state_path = get_state_path(operation_id)
    if state_path.exists():
        state_path.unlink()


def list_state_files() -> list[Path]:
    """
    List all state files.

    Returns:
        List of state file paths
    """
    if not STATE_DIR.exists():
        return []
    return list(STATE_DIR.glob("*.json"))


def load_all_states() -> list[OperationState]:
    """
    Load all state files.

    Returns:
        List of all operation states
    """
    states = []
    for state_path in list_state_files():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                states.append(OperationState.from_dict(data))
        except (json.JSONDecodeError, OSError):
            continue
    return states


def is_orphaned(state: OperationState, max_age_hours: int = 24) -> bool:
    """
    Check if state file is orphaned (old with no active process).

    Args:
        state: OperationState to check
        max_age_hours: Maximum age in hours before considering orphaned

    Returns:
        True if state appears orphaned
    """
    from datetime import datetime, timedelta

    try:
        started = datetime.fromisoformat(state.started_at)
        age = datetime.now() - started
        return age > timedelta(hours=max_age_hours)
    except (ValueError, OSError):
        return False
