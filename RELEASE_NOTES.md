# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

- `flake8` basic checks are enabled now. Most are already covered by `pylint`, but there are a few differences, so you might need to fix your code if `flake8` find some issues.

- `darglint` was replaced by `pydoclint`, `pydoclint` can find a few more issues than `darglint`, so your code might need adjusting.

- `darglint` is not used anymore, but if it is installed, it will make `flake8` run extremely slowly anyways, so it is extremely recommended to uninstall it (`pip uninstall darglint`) and rebuild you `nox` *venvs* if you use `-R`.

- If you are upgrading without regenerating the cookiecutter templates, you'll need to adjust the dependencies accordingly.

### Cookiecutter template

- See the general upgrading section.

## New Features

- `flake8` is now used to check the files.

- `darlint` was replaced by `pydoclint`, which is way faster and detect more issues.

### Cookiecutter template

- Now dependabot updates will be done weekly and grouped by *required* and *optional* for minor and patch updates (major updates are still done individually for each dependency).

- ci: Add debug information when installing pip packages.

  The output of `pip freeze` is printed to be able to more easily debug different behaviours between GitHub workflow runs and local runs.

- See the general new features section.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

<!-- Here bug fixes for cookiecutter specifically -->
