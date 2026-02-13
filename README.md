# git-submit

Automated git push with infinite retry logic and multi-channel notifications.

## Features

- **Infinite retry logic**: Continuously retries git push until success, handling network instability automatically
- **Exponential backoff with jitter**: Intelligent retry intervals to avoid overwhelming networks
- **Multi-channel notifications**: Get notified via email, desktop notifications, or webhooks when push succeeds
- **State persistence**: Resume from where you left off after system reboots or interruptions
- **Zero intervention**: Once triggered, handles all retries automatically

## Installation

```bash
pip install git-submit
```

## Quick Start

```bash
# Initialize configuration
git-submit config init

# Push to GitHub with automatic retries
git-submit push

# Push with custom remote/branch
git-submit push --remote origin --branch main

# Enable desktop notifications
git-submit push --notify-desktop

# Enable email notifications
git-submit push --notify-email
```

## Configuration

Configuration is stored in `~/.git-submit/config.yaml`:

```yaml
retry:
  initial_delay_seconds: 5
  max_backoff_seconds: 300

git:
  remote: origin
  branch: auto  # auto-detect current branch

notifications:
  desktop:
    enabled: true
  email:
    enabled: false
    smtp_host: smtp.example.com
    smtp_port: 587
    username: user@example.com
    password_env: SMTP_PASSWORD
    from: git-submit@example.com
    to: developer@example.com
  webhooks:
    - url: https://hooks.slack.com/services/...
      headers:
        Authorization: "Bearer token"
```

## License

MIT License - see LICENSE file for details.
