# AGENTS.md - AI Coding Agent Instructions

Condensed instructions for AI agents. See [README.md](README.md) and [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

## Project Overview

Python package (3.11+) providing repository configuration and scaffolding for Frequenz projects: cookiecutter templates (actor, api, app, lib, model), nox sessions, protobuf/gRPC utilities, MkDocs and pytest utilities.

**Package:** `src/frequenz/repo/config/` (namespace package, `setuptools_scm` versioning)

## Quick Reference

```sh
# Setup
pip install -e .[dev]              # All dev dependencies
pip install -e .[dev-noxfile]      # Just noxfile deps

# Test
nox -s pytest_max                  # Full test suite
nox -R -s pytest_max               # Reuse venv (faster)
pytest tests/                      # Direct pytest
UPDATE_GOLDEN=1 pytest tests/integration/test_cookiecutter_generation.py::test_golden

# Lint (run before committing)
nox                                # All checks
nox -s formatting                  # black + isort
nox -s mypy                        # Type checking
nox -R -s mypy                     # Reuse venv
```

**Markers:** `integration`, `cookiecutter`

## Project Structure

```
src/frequenz/repo/config/       # Main package (_core.py, nox/, mkdocs/, pytest/, setuptools/, cli/)
tests/                          # Unit tests, tests/integration/ for integration tests
tests_golden/                   # Golden test fixtures
cookiecutter/                   # Cookiecutter templates
```

## Code Patterns

```python
# File header (required)
# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH
"""Module docstring."""

import dataclasses
from typing import Self, assert_never

# Dataclasses: always kw_only + frozen if intended to be immutable
@dataclasses.dataclass(kw_only=True, frozen=True)
class Config:
    """Docstring."""
    opts: CommandsOptions = dataclasses.field(default_factory=CommandsOptions)

# Functions: strict typing, Google docstrings
def func(session: _nox.Session, /, *, flag: bool = True) -> list[str]:
    """Brief description.

    Args:
        session: The nox session.
        flag: Optional flag.

    Returns:
        List of strings.
    """
```

| Type | Convention | Example |
|------|------------|---------|
| Files/functions | snake_case | `api_pages.py`, `find_dirs()` |
| Classes | PascalCase | `RepositoryType` |
| Constants | UPPER_SNAKE | `UPDATE_GOLDEN` |
| Private | `_` prefix | `_impl()` |

**Formatting:** black formatting using 4 spaces (Python), 2 spaces (YAML/TOML/JSON), 88 line length, 100 max, double quotes

When changing files that are regularly reset (like `RELEASE_NOTES.md` or `cookiecutter/migrate.py`), consult the git history to match the style used in the past.

## Commit Messages
- Use imperative mood: "Add", "Fix", "Update"
- Use a 50-character limit for the subject line (can go a bit over if necessary), and wrap body at 80 characters
- Include a brief description of the change in the body if needed, focus on the what and why, and avoid describing how, especially if it is obvious from the code/diff
- Separate changes into logical commits
- Consult the recent git history, specifically of the files being committed, to match style and conventions in commit messages used previously.

## Cookiecutter Template Changes

See [CONTRIBUTING.md](CONTRIBUTING.md#modifying-cookiecutter-templates) for the full workflow. Summary:

1. Edit templates in `cookiecutter/{{cookiecutter.github_repo_name}}/`
2. Update golden files: `UPDATE_GOLDEN=1 pytest tests/integration/test_cookiecutter_generation.py::test_golden`
3. Write migration in `cookiecutter/migrate.py` (idempotent; use `manual_step()` for non-automatable changes)
4. Validate: `python3 cookiecutter/migrate.py && git diff .github/`
5. Update `RELEASE_NOTES.md`
6. Commit separately: templates first, then this repo's migration result
