## Context

**Current State**: Developers experiencing network instability must manually retry `git push` commands repeatedly until successful, wasting time and attention on a task suitable for automation.

**Constraints**:
- Must work cross-platform (Windows, macOS, Linux)
- Must integrate with existing git installations (not replace git)
- Must handle various failure types (network, auth, timeouts) appropriately
- Zero-intervention operation once triggered
- Configuration should be simple for basic use cases

**Stakeholders**: Developers who frequently experience network connectivity issues when pushing to GitHub, particularly in regions with unstable internet connections.

## Goals / Non-Goals

**Goals**:
- Automate git push retries with intelligent backoff to handle transient failures
- Provide user notifications via multiple channels (email, desktop, webhook) on success
- Offer CLI interface with sensible defaults but extensive configurability
- Persist state across process restarts to survive system reboots/interruptions
- Log comprehensively for debugging and transparency

**Non-Goals**:
- Replacing git or implementing git protocol operations (wraps git binary)
- Handling git pull, fetch, or other operations (push only)
- Real-time monitoring dashboard (CLI status queries only)
- Authentication management (relies on existing git credentials)
- Running as a background daemon (foreground CLI process)

## Decisions

### Language and Runtime: Python 3.10+

**Choice**: Python over Node.js, Go, or Rust

**Rationale**:
- **Cross-platform**: Excellent support for Windows/macOS/Linux with minimal platform-specific code
- **Git integration**: Mature libraries (`gitpython` or subprocess wrapper) for invoking git commands
- **Desktop notifications**: `plyer` library provides unified API across platforms (Windows Toast, macOS NotificationCenter, Linux freedesktop)
- **SMTP/HTTP**: Built-in `smtplib` and `httpx`/`requests` eliminate external dependencies for core features
- **Distribution**: Single executable via PyInstaller for easy installation without Python requirement
- **Async support**: `asyncio` for concurrent webhook delivery and non-blocking retry loops

**Alternatives Considered**:
- **Node.js**: Good cross-platform support, but desktop notifications require multiple platform-specific packages
- **Go**: Excellent single-binary distribution, but desktop notification support is fragmented and less mature
- **Rust**: Performance overkill for I/O-bound retry wrapper, ecosystem for desktop notifications less comprehensive

### Architecture: Modular Component Design

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Interface                        │
│  (argparse/Click for command parsing, config file loading)   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Retry Engine Core                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Git Wrapper  │  │ Backoff Logic│  │ State Manager│       │
│  │ (subprocess) │  │ (exponential │  │ (JSON file)  │       │
│  │              │  │  + jitter)   │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              Structured Logging (JSON)               │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │ (on success)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 Notification Dispatcher                       │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐    │
│  │   Email    │  │  Desktop   │  │      Webhook         │    │
│  │ (SMTP)     │  │ (plyer)    │  │    (async HTTP)      │    │
│  └────────────┘  └────────────┘  └──────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Rationale**:
- **Separation of concerns**: Each module (retry engine, notifications, CLI) has single responsibility
- **Testability**: Components can be unit tested in isolation (mock git subprocess, mock SMTP server)
- **Extensibility**: New notification channels or retry strategies can be added without modifying core logic
- **State persistence**: JSON state file allows clean shutdown/resume semantics

### Retry Strategy: Exponential Backoff with Full Jitter

**Choice**: Exponential backoff with randomized jitter (5s initial, 5min max)

**Rationale**:
- **Transient failures**: Network issues are typically self-correcting within seconds/minutes
- **Thundering herd**: Jitter prevents synchronized retries if multiple instances run simultaneously
- **GitHub rate limits**: Exponential backoff avoids triggering API abuse detection
- **No maximum retry count**: Permanent failures (e.g., deleted repo) require manual intervention, so infinite retry is acceptable

**Backoff Formula**: `delay = min(max_backoff, (initial_delay * 2^(attempt-1)) * random.uniform(0.75, 1.25))`

**Alternatives Considered**:
- **Fixed interval**: Simple but inefficient for long-running outages
- **Linear increase**: Predictable but slower to adapt to persistent issues
- **Decorrelated jitter**: More complex algorithm without clear benefit for this use case

### Configuration: YAML with CLI Override

**Choice**: YAML config file at `~/.git-submit/config.yaml` with CLI flag precedence

**Rationale**:
- **Human-readable**: YAML is easier to edit than JSON or TOML for casual users
- **Hierarchy**: Config file for defaults, CLI flags for per-command overrides (common CLI pattern)
- **Validation**: Schema validation (`pydantic` or `jsonschema`) on startup provides early error detection

**Config Structure**:
```yaml
retry:
  initial_delay_seconds: 5
  max_backoff_seconds: 300
  linear: false

git:
  remote: origin
  branch: auto  # auto-detect current branch

notifications:
  email:
    enabled: false
    smtp_host: smtp.example.com
    smtp_port: 587
    username: user@example.com
    password_env: SMTP_PASSWORD  # read from env var
    from: git-submit@example.com
    to: developer@example.com

  desktop:
    enabled: true

  webhooks:
    - url: https://hooks.slack.com/services/...
      headers:
        Authorization: "Bearer token"
```

### State Persistence: File-Based with Atomic Writes

**Choice**: JSON state file at `~/.git-submit/state/<operation-id>.json` with atomic rename

**Rationale**:
- **Crash safety**: Atomic write (temp file + rename) prevents corruption if process killed during write
- **Multi-instance**: Operation ID (based on repo path + branch) allows concurrent operations on different repos
- **Resumability**: Process can be restarted (e.g., system reboot) and resume from last attempt
- **Cleanup**: State file deleted on success,留下的 files indicate stuck operations

**State File Schema**:
```json
{
  "operation_id": "repo-path-branch-name",
  "started_at": "2025-02-13T10:30:00Z",
  "attempts": 42,
  "last_attempt_at": "2025-02-13T11:45:30Z",
  "last_error": "ssh: connect to host github.com port 22: Connection timed out",
  "repository": "/path/to/repo",
  "branch": "main",
  "remote": "origin"
}
```

### Desktop Notifications: Unified Cross-Platform Library

**Choice**: `plyer` library for platform abstraction

**Rationale**:
- **Single API**: One codebase supports Windows (Toast), macOS (NotificationCenter), Linux (freedesktop)
- **Fallback graceful**: If desktop environment unavailable, logs warning without crashing
- **Alternative avoided**: Platform-specific implementations (Windows-only `win10toast`, macOS-only `pyobjc`) would require conditional imports and separate code paths

**Alternatives Considered**:
- **Platform-specific packages**: More control but 3x code complexity
- **webhook-only approach**: Would work but poor UX compared to native notifications

### Notification Delivery: Fire-and-Forget with Error Logging

**Choice**: Notifications are non-blocking; failures are logged but don't affect operation success

**Rationale**:
- **Primary goal**: Git push success is the critical outcome, notifications are informational
- **No retry on notification failure**: SMTP/webhook failures are likely persistent (wrong config, down server)
- **Parallel delivery**: Webhooks sent concurrently via `asyncio.gather()` for speed

### Logging: Structured JSON to File and Optional stdout

**Choice**: JSON log entries written to `~/.git-submit/logs/<operation-id>.log` with optional stdout forwarding

**Rationale**:
- **Machine-parsable**: JSON format enables log aggregation tools (ELK, Splunk, grep -jq)
- **Rotation**: Daily log files prevent unbounded disk usage
- **Stdout modes**: `--verbose` prints human-readable, `--json` prints raw JSON, `--quiet` suppresses
- **Structured fields**: `timestamp`, `level`, `event`, `attempt`, `error`, `repository`, `branch`

## Risks / Trade-offs

### Risk: Infinite retry on permanent errors

**Scenario**: Repository deleted, branch removed, or credentials permanently invalid

**Mitigation**:
- Detect permanent error patterns (e.g., "repository not found", "404", "permission denied")
- Log prominent WARNING message suggesting manual intervention
- Continue retrying (user may fix repo/branch while tool running)
- Future enhancement: Add `--max-retries` flag for users who prefer hard limit

### Risk: Orphaned state files after crashes

**Scenario**: Process killed (SIGKILL, power loss) leaving state files with no active process

**Mitigation**:
- State files include `started_at` timestamp
- `git-submit status --orphaned` command lists stale state files (>24 hours old)
- `git-submit cleanup` command removes orphaned state files
- Future enhancement: PID file + startup check to detect stale operations

### Risk: SMTP credentials in plaintext config

**Scenario**: User stores SMTP password directly in YAML config file

**Mitigation**:
- Document recommended practice: use `password_env` to read from environment variable
- Example config shows secure pattern with comments
- Future enhancement: Support system keychain integration (keyring library)

### Risk: Git executable not in PATH

**Scenario**: Non-standard git installation or Windows without PATH configured

**Mitigation**:
- Detect git availability on startup via `git --version`
- Fail fast with clear error message: "Git not found. Install from https://git-scm.com/"
- Support `GIT_EXEC_PATH` environment variable to override default
- Documentation includes PATH configuration instructions

### Trade-off: Single-threaded retry loop

**Decision**: Sequential retry attempts (not parallel pushes to multiple remotes)

**Rationale**:
- Git push to single remote is inherently sequential operation
- Parallel retries would waste bandwidth and potentially confuse git's state management
- Future enhancement: Support push to multiple remotes (mirror) if requested

## Migration Plan

**Deployment**:
1. Install via `pip install git-submit` or download single binary from releases
2. Run `git-submit config init` to create default config
3. Optional: Configure SMTP/webhook settings in `~/.git-submit/config.yaml`
4. Test: `git-submit push --dry-run` (validates config without pushing)

**Rollback Strategy**:
- Tool is wrapper around git, no modifications to git repository or configuration
- Uninstallation (`pip uninstall git-submit`) removes all tool functionality
- State files (`~/.git-submit/`) can be manually deleted after uninstall
- No git hooks or aliases installed (tool invoked explicitly by user)

**Upgrades**:
- Semantic versioning (SemVer) for API compatibility
- Config file backward compatibility guaranteed across minor versions (0.x.y)
- State file format versioned; migrations run automatically on startup if format changes

## Open Questions

1. **Should we support git push with force (`--force`) flag?**
   - Security concern: Auto-retry with force could be dangerous
   - Likely decision: Require explicit `--force` flag and add confirmation prompt

2. **Should we daemonize and run in background?**
   - Current design: Foreground process with `--follow` flag for monitoring
   - Alternative: Background daemon with status query command
   - Likely decision: Start with foreground, add daemon mode in v0.2.0 if demand exists

3. **Template engine for custom notifications?**
   - Current design: Simple `{{variable}}` substitution via `str.replace()`
   - Alternative: Full template engine (Jinja2) for complex logic
   - Likely decision: Simple substitution sufficient for v0.1.0, Jinja2 if users request advanced features

4. **How to handle SSH key passphrase prompts?**
   - Current design: Relies on git's native SSH agent integration
   - Issue: If SSH agent not running, first retry may hang on passphrase prompt
   - Likely decision: Document SSH agent requirement, detect hang via timeout (future enhancement)
