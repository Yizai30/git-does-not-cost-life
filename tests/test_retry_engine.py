"""Unit tests for retry engine and backoff calculation."""

import pytest
import time

from git_submit.retry_engine import RetryEngine, RetryState


def test_exponential_backoff():
    """Test exponential backoff calculation."""
    engine = RetryEngine(initial_delay_seconds=5, max_backoff_seconds=300, linear=False)

    # Attempt 1: 5s * 2^0 = 5s
    delay = engine.calculate_backoff(1)
    assert delay == 5

    # Attempt 2: 5s * 2^1 = 10s
    delay = engine.calculate_backoff(2)
    assert delay == 10

    # Attempt 3: 5s * 2^2 = 20s
    delay = engine.calculate_backoff(3)
    assert delay == 20

    # Attempt 4: 5s * 2^3 = 40s
    delay = engine.calculate_backoff(4)
    assert delay == 40


def test_backoff_max_cap():
    """Test that backoff is capped at maximum."""
    engine = RetryEngine(initial_delay_seconds=5, max_backoff_seconds=100, linear=False)

    # Should cap at 100s
    delay = engine.calculate_backoff(10)
    assert delay == 100


def test_linear_retry():
    """Test linear retry (constant delay)."""
    engine = RetryEngine(initial_delay_seconds=10, max_backoff_seconds=300, linear=True)

    # All attempts should have same base delay
    for attempt in [1, 2, 3, 4, 5]:
        delay = engine.calculate_backoff(attempt)
        assert 9 <= delay <= 11  # Account for jitter


def test_backoff_jitter():
    """Test that jitter is applied."""
    engine = RetryEngine(initial_delay_seconds=10, max_backoff_seconds=300, linear=False)

    # Multiple calculations should give different results due to jitter
    delays = [engine.calculate_backoff(2) for _ in range(10)]

    # Check variance
    unique_delays = set(int(d) for d in delays)
    assert len(unique_delays) > 1, "Jitter should create variation"


def test_permanent_error_detection():
    """Test detection of permanent error patterns."""
    engine = RetryEngine()

    # Permanent errors
    assert engine.is_permanent_error("repository not found")
    assert engine.is_permanent_error("404 not found")
    assert engine.is_permanent_error("permission denied")

    # Transient errors
    assert not engine.is_permanent_error("connection timed out")
    assert not engine.is_permanent_error("network unreachable")


def test_retry_state_updates():
    """Test that RetryState tracks attempts correctly."""
    state = RetryState()

    assert state.attempt == 0
    assert state.last_error is None

    state.attempt = 5
    state.last_error = "Connection failed"

    assert state.attempt == 5
    assert state.last_error == "Connection failed"
