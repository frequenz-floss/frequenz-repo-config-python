# Frequenz Repository Configuration Release Notes

## Summary

This release adds a new workflow for Dependabot auto-merge and updates mkdocstrings to v2.

## Upgrading

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.14/cookiecutter/migrate.py | python3
```

But you might still need to adapt your code, just have a look at the script output for further instructions.

## New Features

* `mkdocsstrings-python` v2 is now supported.

### Cookiecutter template

- Dependencies have been updated.
- New warning ignores for protobuf gencode versions in pytest.
- Added Dependabot auto-merge workflow using `frequenz-floss/dependabot-auto-approve` action.

## Bug Fixes

### Cookiecutter template

- mkdocstrings: Move `paths` key to the right section in `mkdocs.yml`.
- Fix invalid YAML syntax in Dependabot workflow template.
