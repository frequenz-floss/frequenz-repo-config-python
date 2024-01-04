# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

To upgrade without regenerating the project, you can follow these steps:

- Run the following command to add the new `pylint` ignore rules:

    ```sh
    sed '/  # Checked by flake8/a\  "redefined-outer-name",\n  "unused-import",' pyproject.toml
    ```

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

- Some checks that are already performed by `flake8` are now disabled in `pylint` to avoid double reporting.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

<!-- Here bug fixes for cookiecutter specifically -->
