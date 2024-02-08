# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

To upgrade without regenerating the project, you can follow these steps:

- Run the following command to add the new `pylint` ignore rules:

    ```sh
    sed '/  # Checked by flake8/a\  "redefined-outer-name",\n  "unused-import",' -i pyproject.toml
    ```

- It is recommended to update this rule in your repository to use the new bypass rule for the `Protect version branches` ruleset that allows maintainers to force-merge.

    You can do this by re-importing the ruleset or manually:

    Go to the repository settings -> **Rules** -> **Rulesets** -> **Protect version branches** -> **Bypass list** -> **Add bypass** -> Select **Maintain** role and change the dropdown bypass rule to use **Pull requests** instead of **Always**.

- The `labeler` action was upgraded to 5.0.0. This needs a new configuration file.

    If you haven't diverged much from the default configuration (and you are not using exclusion rules), you can update the configuration file by running this script in the root of your repository:

    ```python
    import sys
    lines = []
    state = "looking"
    with open(".github/labeler.yml", encoding="utf-8") as fin:
        for line in fin:
            if "changed-files:" in line:
                sys.stderr.write("Already fixed, aborting...\n")
                sys.exit(1)
            match state:
                case "looking":
                    if not line.startswith(("#", " ", "\t")) and line.rstrip().endswith(":"):
                        line = f"{line}  - changed-files:\n    - any-glob-to-any-file:\n"
                        state = "in-label"
                case "in-label":
                    if not line.lstrip().startswith("-"):
                        state = "looking"
                    else:
                        line = f"    {line}"
            lines.append(line)
    with open(".github/labeler.yml", "w", encoding="utf-8") as fout:
        fout.writelines(lines)
    ```

    This will update the file in place, you can inspect the changes with `git diff`.

- For API projects, you can manually add instructions to update the `mkdocs.yml` when the `frequenz-api-common` dependency is updated.

    ```sh
    awk -i inplace '/^sed s..frequenz-api-common/ { print; print "sed '"'"'s|https://frequenz-floss.github.io/frequenz-api-common/v[0-9].[0-9]/objects.inv|https://frequenz-floss.github.io/frequenz-api-common/v'"'"'${ver_minor}'"'"'/objects.inv|'"'"' -i mkdocs.yml"; next }1' CONTRIBUTING.md
    ```

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

- Some checks that are already performed by `flake8` are now disabled in `pylint` to avoid double reporting.
- The repository ruleset `Protect version branches` has been updated to allow repository maintainers to skip protection rules in PRs.
- The `labeler` action was upgraded to 5.0.0, which allows for more complex matching rules.
- Instruction were added to update the `mkdocs.yml` when the `frequenz-api-common` dependency is updated.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

<!-- Here bug fixes for cookiecutter specifically -->
