# OVERVIEW
Opinionated repository configuration and scaffolding for Frequenz projects.
Core stack: Python 3.11+, cookiecutter, nox, mkdocs, protobuf/gRPC.

# STRUCTURE
- `src/frequenz/repo/config/`: Main package; nox, mkdocs, pytest, setuptools, CLI helpers.
- `cookiecutter/`: Template sources, hooks, local extensions, migration script.
- `cookiecutter/{{cookiecutter.github_repo_name}}/`: Embedded generated-repo skeleton.
- `tests/`: Unit tests plus `tests/integration/` for template generation.
- `tests_golden/`: Reference outputs for integration tests; generated, do not edit directly.
- `docs/`: MkDocs documentation source tree.
- `.github/`: Workflows, issue templates, release-note templates, migration script template.

# WHERE TO LOOK
- Template author workflow: `cookiecutter/`, `cookiecutter/migrate.py`, `tests/integration/test_cookiecutter_generation.py`.
- Generated scaffold files: `cookiecutter/{{cookiecutter.github_repo_name}}/`.
- Default nox behavior: `src/frequenz/repo/config/nox/default.py`, `nox/session.py`.
- Docs generation/versioning: `src/frequenz/repo/config/mkdocs/`, `docs/_scripts/`, `mkdocs.yml`.
- Template migrations: `cookiecutter/migrate.py`, `.github/cookiecutter-migrate.template.py`.
- Golden-test contract: `tests/integration/test_cookiecutter_generation.py`, `tests_golden/`.
- Release/CI policy: `CONTRIBUTING.md`, `.github/workflows/`, `RELEASE_NOTES.md`, `.github/RELEASE_NOTES.template.md`.

# CONVENTIONS
- Header: License + copyright header required.
- Dataclasses: prefer `kw_only=True`; use `frozen=True` for immutables.
- Strict typing, Google-style docstrings, positional-only/keyword-only when useful.
- Prefer `pyproject.toml` as the canonical configuration source.
- `setuptools_scm` managed; avoid manual version bumps.
- Formatting: Black/isort, double quotes, 4 spaces in Python, 2 spaces in YAML/TOML/JSON.
- `RELEASE_NOTES.md` and `cookiecutter/migrate.py`: reset after a release from templates in `.github/`, consult the git history to match the style used in the past if you need to change them.
- When this project changes, `cookiecutter/` or `src/`, downstream projects are affected. Always add migration steps to `cookiecutter/migrate.py` when necessary.

# ANTI-PATTERNS
- Do not edit `tests_golden/` by hand.
- Do not treat `cookiecutter/{{cookiecutter.github_repo_name}}/` as the live repo root.
- Do not bypass `cookiecutter/migrate.py` when template changes affect existing repos.
- Do not edit generated outputs under `build/` or `site/` as primary sources.
- Do not bypass updating AGENTS.md files when changing structure or conventions.
- Do not bypass updating `docs/` when changing public APIs or user-facing features.
- Do not skip updating `cookiecutter/migrate.py` when changes need to be propagated to existing generated repos.
- Do not add generic repo-agnostic guidance.

# UNIQUE STYLES
- Idempotent migrations via `migrate.py` with `manual_step()` markers.
- Template workflow splits naturally into template edit, golden update, migration result.

# COMMANDS
- `pip install -e .[dev]`: Full dev environment.
- `nox`: Run full tests/checks (formatting, flake8, mypy, pylint, pytest).
- `nox -s pytest_max`: Full test suite.
- `UPDATE_GOLDEN=1 pytest tests/integration/test_cookiecutter_generation.py::test_golden`: Refresh golden fixtures.
- `python3 cookiecutter/migrate.py`: Validate migration logic.
- `mkdocs build`: Build docs locally.
- Consult `CONTRIBUTING.md` for full cookiecutter, docs, and release workflows.
