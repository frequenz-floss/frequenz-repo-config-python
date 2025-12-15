# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.14/cookiecutter/migrate.py | python3
```

But you might still need to adapt your code:

<!-- Here upgrade steps for cookiecutter specifically -->

## New Features

* `mkdocsstrings-python` v2 is now supported.
* Add `grpc_stubs` config option to control which gRPC stubs are generated (`sync_and_async`, `sync_only`, or `async_only`).

### Cookiecutter template

- New warning ignores for protobuf gencode versions in pytest.
- mkdocstrings: Updated the deprecated `import` config key to `inventories` in `mkdocs.yml`.
- Dependencies have been updated.
- Added Dependabot auto-merge workflow using `frequenz-floss/dependabot-auto-approve` action.
- Migration script now creates auto-merge workflow and disables CODEOWNERS review requirement via GitHub API.
- The `import` key in `mkdocs.yml` under `mkdocstrings` has to be renamed to `inventories`.
- The `paths` key in `mkdocs.yml` under `mkdocstrings` has to be moved from the `options` key to the `python` key.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- mkdocstrings: Move `paths` key to the right section in `mkdocs.yml`.
- Migration script: Fix invalid YAML syntax in Dependabot workflow template.
