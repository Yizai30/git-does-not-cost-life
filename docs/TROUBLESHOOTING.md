# Troubleshooting Guide

## Git Not Found

**Error**: `Git not found in PATH. Install from https://git-scm.com/`

**Solution**:
1. Install Git from https://git-scm.com/
2. Restart your terminal/command prompt
3. Verify installation:
   ```bash
   git --version
   ```

**Windows PATH Issue**:
If Git is installed but not found:
1. Open "Environment Variables" (search in Start menu)
2. Edit "Path" variable
3. Add Git installation path (typically: `C:\Program Files\Git\cmd`)
4. Restart terminal

## Configuration Errors

**Error**: `Configuration validation failed`

**Solution**:
Run validation to see detailed errors:
```bash
git-submit config validate
```

Common issues:
- Missing required field
- Invalid value (e.g., negative delay)
- Syntax error in YAML

## SMTP Failures

**Error**: `⚠ Email notification failed: ...`

**Solutions**:

### Wrong Credentials
Verify username and password:
```bash
echo $SMTP_PASSWORD  # Check password is set
```

### Wrong Port
Common SMTP ports:
- **587**: TLS/STARTTLS
- **465**: SSL
- **25**: Unencrypted (not recommended)

Try different port if connection fails.

### Gmail-Specific Issues

1. Enable 2-Factor authentication on your Google Account
2. Create "App Password" at https://myaccount.google.com/apppasswords
3. Use app password in config:
   ```yaml
   email:
     password_env: GMAIL_APP_PASSWORD
   ```
4. Enable "Less secure app access" if required

### Firewall Blocking
Port 587 may be blocked. Try:
- Using port 465 (SSL)
- Disabling firewall temporarily for testing

## Desktop Notifications Not Working

**Error**: `⚠ Desktop notifications unavailable (plyer not installed)`

**Solution**:
```bash
pip install plyer
```

**Linux-Specific**:
Ensure notification daemon is running:
```bash
# Check if notify-send works
notify-send "Test" "Test notification"
```

Install if missing:
```bash
# Ubuntu/Debian
sudo apt-get install libnotify-bin

# Fedora
sudo dnf install libnotify

# Arch
sudo pacman install libnotify
```

## Authentication Failures (401/403)

**Error**: Git push returns `authentication failed` or `permission denied`

**Solutions**:

### SSH Key Issues
1. Verify SSH key is loaded:
   ```bash
   ssh-add -l  # List loaded keys
   ```

2. Add SSH key if not loaded:
   ```bash
   ssh-add ~/.ssh/id_rsa
   ```

3. Start SSH agent if not running:
   ```bash
   # Linux/macOS
   eval "$(ssh-agent -s)"

   # Windows (Git Bash)
   eval $(ssh-agent)
   ```

### Personal Access Token Issues
For GitHub, token may have expired:
1. Go to https://github.com/settings/tokens
2. Generate new token with `repo` scope
3. Update credentials:
   ```bash
   git remote set-url origin https://NEW_TOKEN@github.com/username/repo.git
   ```

### Two-Factor Authentication
If 2FA is enabled, use personal access token instead of password.

## Network Timeouts

**Error**: `ssh: connect to host github.com port 22: Connection timed out`

**Solutions**:

### Proxy Issues
Configure proxy if behind corporate firewall:
```bash
# Set SSH proxy
export GIT_SSH_COMMAND="ssh -o ProxyCommand=nc -X connect -x proxysvr.example.com 3128"

# Or use HTTPS instead
git config --global url.https://github.com/.insteadof ssh://github.com/
```

### Increase Backoff
If network is very slow:
```yaml
retry:
  initial_delay_seconds: 30  # Wait longer before retry
  max_backoff_seconds: 600   # Cap at 10 minutes
```

## State File Issues

**Error**: Operation doesn't resume after restart

**Solution**:
Check if state file exists:
```bash
ls ~/.git-submit/state/
```

Remove orphaned state files:
```bash
git-submit cleanup
```

### Manual State Cleanup
If tool won't start due to corrupted state:
```bash
# List state files
ls ~/.git-submit/state/

# Remove specific state file
rm ~/.git-submit/state/OPERATION_ID.json

# Or clean all orphaned
git-submit cleanup
```

## Repository Not Found

**Error**: `repository not found` or `404`

**Solutions**:

### Check Remote URL
```bash
git remote -v
```

Update if incorrect:
```bash
git remote set-url origin https://github.com/username/correct-repo.git
```

### Verify Repository Exists
Open repository URL in browser to verify it exists.

## Permission Denied

**Error**: `permission denied` on push

**Solutions**:

### Check Repository Access
1. Go to repository on GitHub/Gitee
2. Verify you have push permissions
3. Request access if you don't

### Check Branch Protection
Branch may be protected:
```bash
# Check if main/master is protected
git branch -r
```

Contact repository admin to add you as allowed contributor or disable protection.

## Debug Mode

Enable verbose logging to diagnose issues:
```bash
git-submit push --verbose --follow
```

View logs:
```bash
# Linux/macOS
cat ~/.git-submit/logs/*.log

# Windows
type %USERPROFILE%\.git-submit\logs\*.log
```

## Still Having Issues?

1. Create an issue on GitHub: https://github.com/Yizai30/git-does-not-cost-life/issues
2. Include:
   - OS and version
   - git-submit version
   - Configuration (sanitize passwords!)
   - Error message
   - Logs from `~/.git-submit/logs/`
