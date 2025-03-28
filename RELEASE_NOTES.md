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

- Dependabot config now uses a new grouping that should make upgrades more smooth.

    * We group patch updates as they should always work.
    * We also group minor updates, as it works too for most libraries, typically except libraries that don't have a stable release yet (v0.x.x branch), so we make some exceptions for them.
    * Major updates and dependencies excluded by the above groups are still managed, but they'll create one PR per dependency, as breakage is expected, so it might need manual intervention.
    * Finally, we group some dependencies that are related to each other, and usually needs to be updated together.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

<!-- Here bug fixes for cookiecutter specifically -->
