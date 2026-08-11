# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSLf https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3 -I
```

But you might still need to adapt your code:

<!-- Here upgrade steps for cookiecutter specifically -->

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

- Generated `pyproject.toml` no longer sets `addopts = "-vv"` under `[tool.pytest.ini_options]` as this is too verbose for a default.
- Generated projects enable mypy's `exhaustive-match` error code.
- Removed the dummy DCO workflow for the merge queue, as the DCO GitHub App now runs on `merge_group` events. The `DCO` required status check in the "Protect version branches" ruleset is now pinned to the DCO GitHub App; the migration script removes the workflow and updates the ruleset (via the `gh` CLI) for existing repositories.

## Enhancements

- Improved the docstring documentation and cross-references across the `frequenz.repo.config` package.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

- Fixed several typos and broken code examples in the docstrings.

### Cookiecutter template

<!-- Here bug fixes for cookiecutter specifically -->
