# Frequenz Repository Configuration Release Notes

## Summary

This is a maintenance, template-only, bugfix release.

## Upgrading

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.16.0/cookiecutter/migrate.py | python3
```

## Bug Fixes

### Cookiecutter template

- Added a migration step for api repositories to fix `mkdocs.yml` when the previous `mkdocstrings-python` v2 migration moved only `paths: ["src"]` under `handlers.python.options` but not `paths: ["py"]`.
- Fixed runners for jobs that require Docker and where wrongly converted to `ubuntu-slim` in v0.15.0, changing them back to `ubuntu-24.04` to avoid Docker-related failures. The template and the migration script were both updated to reflect this change.
- Updated the repo-config migration workflow template and migration script so existing repositories also add the `merge_group` trigger and skip the job unless the event is `pull_request_target`, allowing the workflow to be used as a required merge-queue check.
- Added a migration step to remove the copilot review request from the Protect version branch protection rules.  This was also done by v0.15.0 in theory, but the migration step was wrong and didn't update it properly.
