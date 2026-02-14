# git-submit

Automated git push with infinite retry logic and multi-channel notifications.

## Features

- **Infinite retry logic**: Continuously retries git push until success, handling network instability automatically
- **Exponential backoff with jitter**: Intelligent retry intervals to avoid overwhelming networks
- **Multi-channel notifications**: Get notified via email, desktop notifications, or webhooks when push succeeds
- **State persistence**: Resume from where you left off after system reboots or interruptions
- **Zero intervention**: Once triggered, handles all retries automatically
- **Cross-platform**: Works on Windows, macOS, and Linux

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

## Documentation

- [Configuration Reference](docs/CONFIG_REFERENCE.md) - Full configuration options
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Contributing Guidelines](CONTRIBUTING.md) - Development setup

## Repository

- **GitHub**: https://github.com/Yizai30/git-does-not-cost-life
- **Gitee**: https://gitee.com/Yizai30/git-does-not-cost-life

## License

MIT License - see LICENSE file for details.
