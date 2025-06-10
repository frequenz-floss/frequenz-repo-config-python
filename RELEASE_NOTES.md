# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.12/cookiecutter/migrate.py | python3
```

But you might still need to adapt your code:

<!-- Here upgrade steps for cookiecutter specifically -->

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

<!-- Here new features for cookiecutter specifically -->

## Bug Fixes

- Fixed some typos in the docs.
- Fixed wrong comparison for `mike` versions when versions were equal.
- `setuptools.grpc_tools`: Fix wrong passing of include paths when passed via:

    * Command-line: Now extra white-spaces and empty strings are removed, before they were passed to `protoc -I`.
    * `pyproject.toml`: Now an empty array/list can be passed to override the default paths, before this resulted in an empty string being passed to `protoc -I`.

### Cookiecutter template

<!-- Here bug fixes for cookiecutter specifically -->
