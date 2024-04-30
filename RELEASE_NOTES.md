# Frequenz Repository Configuration Release Notes

## Summary



## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

- A new script for migrating to new templates (instead of regenerating all files) is provided. It can't handle the upgrade 100% automatically, but should make the migration process much easier and less error prone.

  To run it, the simplest way is to fetch it from GitHub and run it directly:

  ```console
  curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.10.0/cookiecutter/migrate.sh | sh
  ```

  Make sure the version you want to migrate to is correct in the URL.

  For jumping multiple versions you should run the script multiple times, once for each version.

  And remember to follow any manual instructions for each run.

## New Features

- A new GitHub ruleset is provided to configure the merge queue, so branch protection rules are not needed anymore.
- Nox will use the uv backend when available, which should make it a lot faster.

### Cookiecutter template

<!-- Here new features for cookiecutter specifically -->

## Enhancements

- The generated docs now show the symbol type in the table of contents.

### Cookiecutter template

- The `Markdown` dependency was bumped so we don't need to add a `type: ignore` due to incorrect type hints.
- The generated docs now show the symbol type in the table of contents.
- The dependecies were updated to the latest versions.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

<!-- Here bug fixes for cookiecutter specifically -->
