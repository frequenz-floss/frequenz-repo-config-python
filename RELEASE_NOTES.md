# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3
```

But you might still need to adapt your code:

<!-- Here upgrade steps for cookiecutter specifically -->

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

<!-- Here new features for cookiecutter specifically -->

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- Added a migration step for api repositories to fix `mkdocs.yml` when the previous `mkdocstrings-python` v2 migration moved only `paths: ["src"]` under `handlers.python.options` but not `paths: ["py"]`.
- Fixed runners for jobs that require Docker and where wrongly converted to `ubuntu-slim` in v0.15.0, changing them back to `ubuntu-24.04` to avoid Docker-related failures. The template and the migration script were both updated to reflect this change.
- Updated the repo-config migration workflow template and migration script so existing repositories also add the `merge_group` trigger and skip the job unless the event is `pull_request_target`, allowing the workflow to be used as a required merge-queue check.
- Added a migration step to remove the copilot review request from the Protect version branch protection rules.  This was also done by v0.15.0 in theory, but the migration step was wrong and didn't update it properly.
