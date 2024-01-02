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

- It is recommended to update this rule in your repository to use the new bypass rule for the `Protect version branches` ruleset that allows maintainers to force-merge.

    You can do this by re-importing the ruleset or manually:

    Go to the repository settings -> **Rules** -> **Rulesets** -> **Protect version branches** -> **Bypass list** -> **Add bypass** -> Select **Maintain** role and change the dropdown bypass rule to use **Pull requests** instead of **Always**.

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

- Some checks that are already performed by `flake8` are now disabled in `pylint` to avoid double reporting.
- The repository ruleset `Protect version branches` has been updated to allow repository maintainers to skip protection rules in PRs.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

<!-- Here bug fixes for cookiecutter specifically -->
