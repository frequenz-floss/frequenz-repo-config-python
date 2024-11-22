# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

- The `nox` default `pytest` session doesn't pass `-W=all -vv` to `pytest` anymore. You can use the `pyproject.toml` file to configure default options for `pytest`, for example:

    ```toml
    [tool.pytest.ini_options]
    addopts = "-W=all -vv"
    ```

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

<!-- Here new features for cookiecutter specifically -->

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

<!-- Here bug fixes for cookiecutter specifically -->
