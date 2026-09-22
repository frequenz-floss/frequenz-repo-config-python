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

<!-- Here new features for cookiecutter specifically -->

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- The mkdocstrings `paths` key in `mkdocs.yml` is back under `handlers.python`, where it belongs. Since v0.14.0 the template generated it directly under `handlers`, where mkdocstrings reads it as a handler name and aborts the build with `ModuleNotFoundError: No module named 'mkdocstrings_handlers.paths'`, so newly generated projects could not build their documentation. Existing projects are unaffected, as previous migration steps always moved the key to the correct place. The migration script now fixes both this location and the older `handlers.python.options` one.
