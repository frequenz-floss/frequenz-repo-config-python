# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

- The `nox` default `pytest` session doesn't pass `-W=all -vv` to `pytest` anymore. You can use the `pyproject.toml` file to configure default options for `pytest`, for example:

    ```toml
    [tool.pytest.ini_options]
    addopts = "-W=all -Werror -Wdefault::DeprecationWarning -Wdefault::PendingDeprecationWarning -vv"
    ```

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates. But you might still need to adapt your code:

- `pytest` now uses `-Werror` by default (but still treat deprecations as normal warnings), so if your tests run with warnings, they will now be turned to errors, and you'll need to fix them.

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

- `pytest` now uses `-Werror -Wdefault::DeprecationWarning -Wdefault::PendingDeprecationWarning` by default. Deprecations are still treated as warnings, as when testing with the `pytest_min` session is normal to get deprecation warnings as we are using old versions of dependencies.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

<!-- Here bug fixes for cookiecutter specifically -->
