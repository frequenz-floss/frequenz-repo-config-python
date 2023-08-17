# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

- If your replay file contains a `_extensions` key, you should remove it, as you most likely want to use the extensions declared by the repo-config cookiecutter template you are upgrading to, otherwise you could get errors about missing extensions.

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template


- Generated project's dependencies were bumped.

- Move `TODO`s so they are in their own line.

  This makes it easier to upgrade projects to new templates, as removing whole lines is easier than having to edit them.

- Clean up `_extensions` from the generated replay file.

  It is not needed in the generated project, we always want to use the ones from the repo-config template.

  This should ease upgrading projects, making it less likely to have errors about missing extensions.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- Properly label `conftest.py` files.
