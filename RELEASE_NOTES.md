# Frequenz Repository Configuration Release Notes

## Summary

This is a minor release with some documentation improvements, new GitHub ruleset and a few bug fixes.

## Upgrading

### Cookiecutter template

You can follow these steps to upgrade without regenerating the whole project, if you kept the default project structure and configuration:

* Update the `frequenz-repo-config` dependencies in `pyproject.toml` to 0.8.0.

* Run in the root directory of your project:

    ```sh
    sed -i '/custom_templates: templates/d' mkdocs.yml
    sed -i '/  "too-few-public-methods",/a \  "too-many-return-statements",' pyproject.toml
    find -type f -exec sed -i 's/Freqenz/Frequenz/g' {} +
    cat <<EOF >> .gitignore

    # Auto-generated python files from the protocol buffer compiler
    py/**/*_pb2.py
    py/**/*_pb2.pyi
    py/**/*_pb2_grpc.py
    py/**/*_pb2_grpc.pyi
    EOF
    ```

* Optionally go to the GitHub project's settings and replace branch protection rules with the new rulesets. See the new [GitHub configuration guide](https://frequenz-floss.github.io/frequenz-repo-config-python/v0.8/user-guide/start-a-new-project/github-configuration/#branches) for more details.

## New Features

- New GitHub rulesets are provided with the recommended configuration to protect branches and tags.
- The documentation is restructured into a more organized, easier-to-navigate user guide.
- Documentation on how to configure the GitHub project and PyPI package is now provided.

### Cookiecutter template

- The `pylint` check `too-many-return-statements` is now disabled by default.
- Generated protobuf files are now ignored by Git.

## Bug Fixes

### Cookiecutter template

* Fix typo: `Freqenz` -> `Frequenz`
* Fix `mkdocs.yml` to avoid specifying `custom_templates` for `mkdocstrings` as it is unused and is checked for existence in newer versions.
* Fix paths that are not translated properly from the python package name (#198)
* Fix outdated `frequenz-repo-config` dependency
