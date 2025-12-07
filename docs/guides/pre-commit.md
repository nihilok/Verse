# Pre-commit Hooks Setup

This project uses [pre-commit](https://pre-commit.com/) to automatically run code quality checks before each commit.

## What's Included

The pre-commit hooks will automatically run:

### Backend (Python)
- **Ruff** - Fast Python linter and formatter
  - Automatically fixes common issues
  - Checks for code style violations
  - Runs formatting

### Frontend (TypeScript/JavaScript)
- **ESLint** - Lints and fixes JavaScript/TypeScript code
- **Prettier** - Formats code for consistency

### General
- Trim trailing whitespace
- Fix end-of-file issues
- Check YAML syntax
- Check for large files
- Check for merge conflicts

## Installation

Pre-commit hooks are automatically installed when you set up the project. If you need to install them manually:

```bash
# Install pre-commit hooks
pre-commit install
```

## Usage

### Automatic (Recommended)
The hooks run automatically on `git commit`. If any issues are found:
1. The commit will be blocked
2. Fixable issues will be automatically corrected
3. You'll need to review the changes and commit again

### Manual
You can run the hooks manually on all files:

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Run a specific hook
pre-commit run ruff --all-files
pre-commit run eslint --all-files
pre-commit run prettier --all-files
```

## Configuration

### Ruff (Backend)
Configuration is in `backend/ruff.toml`. Key settings:
- Line length: 110 characters
- Target: Python 3.13
- Enabled rules: pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, flake8-bugbear, and more
- Ignores FastAPI's `Depends()` pattern (B008)

### ESLint (Frontend)
Configuration is in `frontend/eslint.config.js` and `frontend/.eslintrc.json`.

### Prettier (Frontend)
Uses default Prettier configuration.

### Pre-commit
Main configuration is in `.pre-commit-config.yaml` at the project root.

## Updating Hooks

To update the pre-commit hooks to their latest versions:

```bash
pre-commit autoupdate
```

## Skipping Hooks (Not Recommended)

In rare cases where you need to skip the hooks:

```bash
# Skip all hooks
git commit --no-verify

# Or use the SKIP environment variable for specific hooks
SKIP=eslint git commit -m "message"
```

## Troubleshooting

### Hooks not running
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Cache issues
```bash
# Clean and reinstall
pre-commit clean
pre-commit install --install-hooks
```

### Frontend path issues
If Prettier or ESLint fail with path errors, ensure you're in the project root and that `bun` is installed.

## CI Integration

The same checks run in CI (GitHub Actions), so passing pre-commit locally ensures your PR will pass CI checks.
