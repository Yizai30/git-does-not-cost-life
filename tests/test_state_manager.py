"""Unit tests for state file persistence."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from git_submit.state_manager import (
    create_state,
    save_state,
    load_state,
    delete_state,
    generate_operation_id,
    OperationState,
    is_orphaned,
)


def test_generate_operation_id():
    """Test operation ID generation."""
    # Same repo+branch should give same ID
    id1 = generate_operation_id("/path/to/repo", "main")
    id2 = generate_operation_id("/path/to/repo", "main")

    assert id1 == id2

    # Different branch should give different ID
    id3 = generate_operation_id("/path/to/repo", "develop")
    assert id1 != id3


def test_save_and_load_state():
    """Test saving and loading state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        from git_submit.state_manager import STATE_DIR

        # Override state dir
        original_state_dir = STATE_DIR
        STATE_DIR.__class__.state_dir = Path(tmpdir)  # type: ignore

        try:
            state = create_state(
                repository="/path/to/repo",
                branch="main",
                remote="origin",
            )

            save_state(state)

            # Load and verify
            loaded = load_state(state.operation_id)
            assert loaded is not None
            assert loaded.operation_id == state.operation_id
            assert loaded.repository == "/path/to/repo"
            assert loaded.branch == "main"
            assert loaded.remote == "origin"
            assert loaded.attempts == 0
        finally:
            # Restore
            STATE_DIR.__class__.state_dir = original_state_dir  # type: ignore


def test_delete_state():
    """Test deleting state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from git_submit.state_manager import STATE_DIR

        original_state_dir = STATE_DIR
        STATE_DIR.__class__.state_dir = Path(tmpdir)  # type: ignore

        try:
            state = create_state(repository="/path", branch="main", remote="origin")
            save_state(state)

            state_path = STATE_DIR / f"{state.operation_id}.json"
            assert state_path.exists()

            delete_state(state.operation_id)
            assert not state_path.exists()

            # Loading should return None
            loaded = load_state(state.operation_id)
            assert loaded is None
        finally:
            STATE_DIR.__class__.state_dir = original_state_dir  # type: ignore


def test_is_orphaned():
    """Test orphaned state detection."""
    # Recent state
    recent_state = OperationState(
        operation_id="test-recent",
        started_at=(datetime.now() - timedelta(hours=1)).isoformat(),
        attempts=5,
        last_attempt_at=datetime.now().isoformat(),
        last_error="test",
        repository="/path",
        branch="main",
        remote="origin",
    )
    assert not is_orphaned(recent_state, max_age_hours=24)

    # Old state
    old_state = OperationState(
        operation_id="test-old",
        started_at=(datetime.now() - timedelta(hours=48)).isoformat(),
        attempts=5,
        last_attempt_at=datetime.now().isoformat(),
        last_error="test",
        repository="/path",
        branch="main",
        remote="origin",
    )
    assert is_orphaned(old_state, max_age_hours=24)
