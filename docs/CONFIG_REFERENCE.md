# Configuration Reference

git-submit uses a YAML configuration file located at `~/.git-submit/config.yaml`.

## Configuration File Location

- **Linux/macOS**: `~/.git-submit/config.yaml`
- **Windows**: `C:\Users\YourUsername\.git-submit\config.yaml`

Create default configuration:
```bash
git-submit config init
```

## Configuration Schema

```yaml
# Retry settings
retry:
  initial_delay_seconds: 5      # Initial delay before first retry (1-3600)
  max_backoff_seconds: 300        # Maximum backoff interval (1-86400)
  linear: false                   # Use constant delay instead of exponential

# Git settings
git:
  remote: origin                  # Git remote to push to
  branch: auto                    # Branch name ('auto' = detect current)

# Notification settings
notifications:
  desktop:
    enabled: true                   # Enable desktop notifications

  email:
    enabled: false                  # Enable email notifications
    smtp_host: smtp.example.com         # SMTP server hostname
    smtp_port: 587                    # SMTP server port (1-65535)
    username: your-email@example.com      # SMTP username
    password_env: SMTP_PASSWORD         # Environment var with password
    from_address: git-submit@example.com    # From email address
    to_address: your-email@example.com      # To email address

  webhooks:
    - url: https://hooks.slack.com/services/YOUR/WEBHOOK
      headers:                      # Optional HTTP headers
        Authorization: "Bearer YOUR_TOKEN"
```

## Retry Settings

### initial_delay_seconds

- **Type**: Integer
- **Default**: `5`
- **Range**: 1-3600
- **Description**: Initial delay in seconds before first retry attempt

Example:
```yaml
retry:
  initial_delay_seconds: 10  # Wait 10s before first retry
```

### max_backoff_seconds

- **Type**: Integer
- **Default**: `300`
- **Range**: 1-86400
- **Description**: Maximum backoff interval cap in seconds

Example:
```yaml
retry:
  max_backoff_seconds: 600  # Cap backoff at 10 minutes
```

### linear

- **Type**: Boolean
- **Default**: `false`
- **Description**: Use constant delay instead of exponential backoff

Example:
```yaml
retry:
  linear: true  # Same delay for every retry
```

## Git Settings

### remote

- **Type**: String
- **Default**: `origin`
- **Description**: Git remote name to push to

Example:
```yaml
git:
  remote: upstream  # Push to 'upstream' remote
```

### branch

- **Type**: String
- **Default**: `auto`
- **Description**: Branch name to push. Use `auto` to detect current branch automatically.

Example:
```yaml
git:
  branch: main  # Always push to main branch
```

## Notification Settings

### Desktop Notifications

Desktop notifications use native OS APIs:
- **Windows**: Windows Toast notifications
- **macOS**: NotificationCenter
- **Linux**: freedesktop notification daemon

Configuration:
```yaml
notifications:
  desktop:
    enabled: true
```

### Email Notifications

Email notifications require SMTP server configuration.

Configuration:
```yaml
notifications:
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    username: your-email@gmail.com
    password_env: GMAIL_PASSWORD  # Environment variable name
    from_address: git-submit@gmail.com
    to_address: your-email@gmail.com
```

**Important**: Store passwords in environment variables, not in the config file directly.

Set environment variable:
```bash
export GMAIL_PASSWORD="your-app-password"
```

### Webhook Notifications

Webhooks are HTTP POST requests sent when push succeeds.

Configuration:
```yaml
notifications:
  webhooks:
    - url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      headers:
        Content-Type: "application/json"
        Authorization: "Bearer YOUR_TOKEN"
    - url: https://discord.com/api/webhooks/YOUR/WEBHOOK
      headers:
        Authorization: "Bot YOUR_TOKEN"
```

Multiple webhooks supported. All are triggered on success.

**Payload Format**:
```json
{
  "status": "success",
  "repository": "/path/to/repo",
  "branch": "main",
  "commit_sha": "abc123de",
  "attempts": 5,
  "duration": 123.45,
  "timestamp": "2025-02-13T10:30:00Z"
}
```

## Environment Variables

### SMTP_PASSWORD

Password for SMTP authentication. Referenced by `password_env` in config.

Example:
```bash
export SMTP_PASSWORD="your-secure-password"
```

### GIT_EXEC_PATH

Override git binary location (optional).

Example:
```bash
export GIT_EXEC_PATH="/usr/local/bin/git"
```

## Examples

### Email Only
```yaml
retry:
  initial_delay_seconds: 10

notifications:
  desktop:
    enabled: false
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    username: your-email@gmail.com
    password_env: GMAIL_PASSWORD
    from_address: your-email@gmail.com
    to_address: your-email@gmail.com
```

### Desktop + Slack Webhook
```yaml
notifications:
  desktop:
    enabled: true
  webhooks:
    - url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Desktop + Discord Webhook
```yaml
notifications:
  desktop:
    enabled: true
  webhooks:
    - url: https://discord.com/api/webhooks/YOUR/WEBHOOK
      headers:
        Authorization: "Bot YOUR_TOKEN"
```
