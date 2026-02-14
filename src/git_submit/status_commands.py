"""Status and cleanup commands."""

import sys
from datetime import datetime

from git_submit.state_manager import (
    load_state,
    delete_state,
    list_state_files,
    load_all_states,
    is_orphaned,
    OperationState,
)
from git_submit.logging import Logger, LogLevel, LogEntry


def cmd_status(orphaned: bool = False) -> int:
    """Show operation status."""
    if orphaned:
        # List orphaned state files
        states = load_all_states()
        orphaned = [s for s in states if s and is_orphaned(s)]

        if not orphaned:
            print("No orphaned state files found.")
            return 0

        print(f"Orphaned state files ({len(orphaned)}):")
        for state in orphaned:
            age = (datetime.now() - datetime.fromisoformat(state.started_at)).days
            print(f"  - {state.operation_id}: {state.repository}/{state.branch} ({age} days old)")
        return 0
    else:
        # Show active operation
        states = load_all_states()
        active = [s for s in states if s and not is_orphaned(s)]

        if not active:
            print("No active operations found.")
            return 0

        print(f"Active operations ({len(active)}):")
        for state in active:
            print(f"  - {state.operation_id}:")
            print(f"      Repository: {state.repository}")
            print(f"      Branch: {state.branch}")
            print(f"      Attempts: {state.attempts}")
            print(f"      Started: {state.started_at}")
            if state.last_error:
                error_preview = state.last_error[:80] + "..." if len(state.last_error) > 80 else state.last_error
                print(f"      Last error: {error_preview}")

        return 0


def cmd_cleanup() -> int:
    """Remove orphaned state files."""
    states = load_all_states()
    orphaned = [s for s in states if s and is_orphaned(s)]

    if not orphaned:
        print("No orphaned state files to clean up.")
        return 0

    for state in orphaned:
        delete_state(state.operation_id)

    print(f"Removed {len(orphaned)} orphaned state file(s).")
    return 0


def cmd_history() -> int:
    """Show recent operations."""
    from git_submit.logging import tail_log, LOG_DIR

    # Get all log files
    log_files = list(LOG_DIR.glob("*.log"))

    if not log_files:
        print("No operation history found.")
        return 0

    # Sort by modification time
    log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Show last 10 operations
    print("Recent operations (last 10):")
    for log_file in log_files[:10]:
        entries = tail_log(log_file, lines=1)
        if entries:
            entry = entries[0]
            timestamp = entry.data.get("timestamp", "")
            event = entry.data.get("event", "")
            print(f"  - [{timestamp}] {event}")

    return 0
