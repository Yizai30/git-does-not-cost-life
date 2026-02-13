## 1. Project Setup and Infrastructure

- [x] 1.1 Initialize Python project structure with `src/` and `tests/` directories
- [x] 1.2 Create `pyproject.toml` with project metadata, dependencies (pyyaml, plyer, httpx), and CLI entry point
- [x] 1.3 Set up development environment: virtualenv, pytest for testing, black for formatting, mypy for type checking
- [x] 1.4 Create GitHub repository with README, LICENSE, and basic documentation structure
- [x] 1.5 Configure CI/CD pipeline (GitHub Actions) for running tests and building distributions

## 2. Configuration Management

- [x] 2.1 Define configuration data models using Pydantic for validation (retry settings, git settings, notification settings)
- [x] 2.2 Implement config file loader for YAML at `~/.git-submit/config.yaml` with default fallback values
- [x] 2.3 Implement environment variable interpolation for sensitive fields (e.g., `password_env: SMTP_PASSWORD`)
- [x] 2.4 Add CLI flag parser with precedence: CLI flags > config file > defaults
- [x] 2.5 Implement `git-submit config init` command to create default config file with documented examples
- [x] 2.6 Implement `git-submit config edit` command to open config in default editor
- [x] 2.7 Implement `git-submit config validate` command with schema validation and error reporting
- [x] 2.8 Implement `git-submit config show` command to display effective configuration

## 3. Git Integration and Retry Engine

- [x] 3.1 Create git wrapper module using subprocess to invoke `git push` commands
- [x] 3.2 Implement git availability check (`git --version`) with fail-fast error message
- [x] 3.3 Implement branch detection (`git branch --show-current`) with fallback to config default
- [x] 3.4 Implement retry loop with exponential backoff: `delay = min(max, initial * 2^(n-1))`
- [x] 3.5 Add randomized jitter (±25%) to backoff intervals to prevent thundering herd
- [x] 3.6 Implement success detection: check git push exit code 0 and optional `git ls-remote` verification
- [x] 3.7 Capture and log git stdout/stderr for each retry attempt
- [x] 3.8 Detect permanent error patterns (repository not found, 404, permission denied) with WARNING logs
- [x] 3.9 Implement `--dry-run` flag for testing without actual git push

## 4. State Persistence and Recovery

- [x] 4.1 Design state file schema with fields: operation_id, started_at, attempts, last_attempt_at, last_error, repository, branch, remote
- [x] 4.2 Implement atomic state file write (write to temp file + rename) for crash safety
- [x] 4.3 Create state directory structure at `~/.git-submit/state/`
- [x] 4.4 Generate unique operation ID based on repository path + branch name
- [x] 4.5 Implement state file creation on operation start
- [x] 4.6 Implement state file update after each retry attempt
- [x] 4.7 Implement state file cleanup on successful completion
- [x] 4.8 Implement resume logic: detect existing state file on startup and continue retrying
- [x] 4.9 Implement `git-submit status` command to display active operation details
- [x] 4.10 Implement `git-submit status --orphaned` to list stale state files (>24 hours old)
- [x] 4.11 Implement `git-submit cleanup` command to remove orphaned state files

## 5. Structured Logging

- [x] 5.1 Design log entry schema with fields: timestamp, level, event, attempt, error, repository, branch
- [x] 5.2 Create log directory structure at `~/.git-submit/logs/` with daily rotation
- [x] 5.3 Implement JSON log writer with structured formatting
- [x] 5.4 Implement log levels: DEBUG, INFO, WARNING, ERROR
- [x] 5.5 Add logging for retry attempts (attempt number, timestamp, backoff interval)
- [x] 5.6 Add logging for git push output (stdout/stderr capture)
- [x] 5.7 Add logging for success completion (duration, attempt count, commit SHA)
- [x] 5.8 Implement `--verbose` flag: print human-readable log entries to stdout
- [x] 5.9 Implement `--json` flag: print raw JSON log entries to stdout
- [x] 5.10 Implement `--quiet` flag: suppress all stdout output (logs only written to file)
- [x] 5.11 Implement `--follow` flag: tail log file in real-time during retry loop

## 6. Email Notifications

- [x] 6.1 Create email notification module using Python's built-in `smtplib`
- [x] 6.2 Implement SMTP connection with TLS/SSL support
- [x] 6.3 Implement SMTP authentication with username/password from config
- [x] 6.4 Create default email template with variables: repo, branch, commit, attempts, duration, timestamp
- [x] 6.5 Implement simple `{{variable}}` template substitution for custom email templates
- [x] 6.6 Add email template validation on startup (check required variables present)
- [x] 6.7 Implement graceful error handling: log SMTP failures without crashing main operation
- [x] 6.8 Add `--notify-email` CLI flag to enable email notifications
- [x] 6.9 Add `--no-notify` CLI flag to disable all notifications

## 7. Desktop Notifications

- [x] 7.1 Install and configure `plyer` library for cross-platform desktop notifications
- [x] 7.2 Implement Windows toast notification (via plyer's Windows backend)
- [x] 7.3 Implement macOS NotificationCenter notification (via plyer's macOS backend)
- [x] 7.4 Implement Linux freedesktop notification (via plyer's Linux backend)
- [x] 7.5 Create default notification content: title "GitHub Push Successful", body with repo/branch, click action
- [x] 7.6 Implement graceful fallback: log warning if desktop notifications unavailable
- [x] 7.7 Add `--notify-desktop` CLI flag to enable desktop notifications

## 8. Webhook Notifications

- [x] 8.1 Create webhook notification module using `httpx` for async HTTP requests
- [x] 8.2 Define default webhook payload schema: {status, repository, branch, commit_sha, attempts, duration, timestamp}
- [x] 8.3 Implement `{{variable}}` JSON template substitution for custom webhook payloads
- [x] 8.4 Implement concurrent webhook delivery to multiple URLs using `asyncio.gather()`
- [x] 8.5 Add support for custom HTTP headers (e.g., Authorization) in webhook config
- [x] 8.6 Set 10-second timeout for webhook requests to prevent hanging
- [x] 8.7 Implement graceful error handling: log non-2xx responses without retrying
- [x] 8.8 Add `--notify-webhook <url>` CLI flag to enable webhook notifications (multiple allowed)

## 9. CLI Interface and Commands

- [x] 9.1 Implement main `git-submit` command with help text and usage examples
- [x] 9.2 Implement `git-submit push` command with flags: --remote, --branch, --all, --retry-delay, --max-backoff, --linear-retry
- [x] 9.3 Implement notification channel flags: --notify-email, --notify-desktop, --notify-webhook, --no-notify
- [x] 9.4 Implement logging control flags: --verbose, --quiet, --json, --follow
- [x] 9.5 Add `--force` flag support with confirmation prompt for dangerous operations
- [x] 9.6 Implement auto-detection of current branch when --branch flag omitted
- [x] 9.7 Implement `git-submit push --all` to push all branches via `git push --all`
- [x] 9.8 Implement command-specific help: `git-submit push --help` shows push-related flags
- [x] 9.9 Implement `git-submit help examples` command displaying common usage patterns
- [x] 9.10 Implement `git-submit history` command to list recent completed operations with timestamps

## 10. Error Handling and Edge Cases

- [x] 10.1 Handle git executable not in PATH: detect on startup, fail fast with installation instructions
- [x] 10.2 Support `GIT_EXEC_PATH` environment variable to override git binary location
- [x] 10.3 Handle invalid config file syntax: validate on startup, show clear error message
- [x] 10.4 Handle missing required config fields: use defaults, log warning
- [x] 10.5 Handle template validation errors: fail fast with missing variable hints
- [x] 10.6 Handle network timeouts: increase backoff interval and retry
- [x] 10.7 Handle authentication failures (401/403): retry indefinitely assuming credentials may refresh
- [x] 10.8 Handle keyboard interrupts (Ctrl+C): cleanup state files, exit gracefully with message

## 11. Testing

- [x] 11.1 Write unit tests for configuration loading and validation
- [x] 11.2 Write unit tests for exponential backoff calculation with jitter
- [x] 11.3 Write unit tests for state file persistence (create, update, cleanup)
- [x] 11.4 Write unit tests for log entry formatting and file rotation
- [ ] 11.5 Write unit tests for email notification with mocked SMTP server
- [ ] 11.6 Write unit tests for webhook notification with mocked HTTP responses
- [ ] 11.7 Write integration tests for retry loop with simulated git failures
- [ ] 11.8 Write integration tests for resume functionality (state file recovery)
- [ ] 11.9 Add end-to-end test: full workflow with real git repository (optional, manual test)
- [x] 11.10 Set up test coverage reporting (aim for >80% coverage)

## 12. Documentation

- [ ] 12.1 Write README.md with installation instructions, quick start guide, and examples
- [ ] 12.2 Document configuration file schema with all options and defaults
- [ ] 12.3 Create CLI reference documentation for all commands and flags
- [ ] 12.4 Write troubleshooting guide for common issues (git not found, SMTP failures, etc.)
- [ ] 12.5 Document SSH agent requirement for key-based authentication
- [ ] 12.6 Add example configuration files for common use cases (email only, desktop + webhook, etc.)
- [ ] 12.7 Create CHANGELOG.md following Keep a Changelog format
- [ ] 12.8 Add Contributing Guidelines for developers

## 13. Distribution and Packaging

- [ ] 13.1 Configure PyInstaller spec file for creating standalone executables
- [ ] 13.2 Set up GitHub Actions workflow to build wheels and source distributions
- [ ] 13.3 Set up GitHub Actions workflow to build standalone executables (Windows, macOS, Linux)
- [ ] 13.4 Create release automation script for tagging and publishing to PyPI
- [ ] 13.5 Test installation from PyPI with `pip install git-submit`
- [ ] 13.6 Test standalone executable on all three platforms

## 14. Release Preparation

- [ ] 14.1 Version bump to 0.1.0 in pyproject.toml
- [ ] 14.2 Update README with installation instructions and feature summary
- [ ] 14.3 Create GitHub release with release notes and binary downloads
- [ ] 14.4 Publish package to PyPI
- [ ] 14.5 Announce tool on relevant platforms (Hacker News, Reddit r/git, etc.)
