# Frequenz Repository Configuration Release Notes

## Summary

This release migrates lightweight GitHub Actions workflow jobs to use the new cost-effective `ubuntu-slim` runner.
It also updates cookiecutter pyproject license metadata to SPDX expressions to avoid setuptools deprecation warnings.

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.14.0/cookiecutter/migrate.py | python3
```

But you might still need to adapt your code:

<!-- Here upgrade steps for cookiecutter specifically -->

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

- Migrated lightweight workflow jobs to use the new `ubuntu-slim` runner for cost savings.
  The following jobs now use `ubuntu-slim`:
  - `ci.yaml`: `protolint`, `nox-all`, `test-installation-all`, `create-github-release`, `publish-to-pypi`
  - `ci-pr.yaml`: `protolint`
  - `auto-dependabot.yaml`: `auto-merge`
  - `release-notes-check.yml`: `check-release-notes`
  - `dco-merge-queue.yml`: `DCO`
  - `labeler.yml`: `Label`

- Added the [`flake8-datetimez`](https://github.com/pjknkda/flake8-datetimez) plugin to the `flake8` session. This plugin prevents accidental use of naive `datetime` objects by flagging calls that create or return datetimes without timezone information.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- Switched `project.license` to SPDX expressions and added `project.license-files`.
  This removes deprecated setuptools license metadata and avoids build warnings.
