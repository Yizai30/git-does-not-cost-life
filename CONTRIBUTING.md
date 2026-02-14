# Contributing to git-submit

Thank you for your interest in contributing to git-submit!

## Development Setup

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/git-does-not-cost-life.git
   cd git-does-not-cost-life
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Create a virtual environment for development (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

## Running Tests

Execute the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src --cov-report=html
```

## Code Style

This project uses:
- **Black** for code formatting (line length: 100)
- **mypy** for type checking
- **ruff** for linting

Format code:
```bash
black src/
```

Check types:
```bash
mypy src/
```

Lint:
```bash
ruff check src/
```

## Commit Messages

Follow the conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Example:
```
feat: add support for custom notification templates

Add ability for users to provide custom email and webhook templates
with {{variable}} substitution for personalization.

Co-Authored-By: Your Name <your.email@example.com>
```

## Submitting Changes

1. Create a descriptive branch name:
   ```bash
   git checkout -b feature/add-xyz-support
   ```
2. Commit your changes with clear messages
3. Push to your fork:
   ```bash
   git push origin feature/add-xyz-support
   ```
4. Create a pull request on GitHub

## Project Structure

```
git-submit/
├── src/
│   └── git_submit/
│       ├── __init__.py
│       ├── cli.py              # Main CLI entry point
│       ├── cli_args.py         # Argument parsing
│       ├── config.py            # Pydantic models
│       ├── config_loader.py     # YAML loading
│       ├── config_commands.py    # Config management commands
│       ├── git_wrapper.py      # Git subprocess wrapper
│       ├── retry_engine.py      # Retry logic with backoff
│       ├── state_manager.py     # State persistence
│       ├── logging.py           # Structured logging
│       └── notifications.py     # Email, desktop, webhook
├── tests/                     # Test suite
├── openspec/                  # Design artifacts
├── pyproject.toml             # Project config
└── README.md                  # Documentation
```

## Questions?

Feel free to open an issue on GitHub for discussion.
