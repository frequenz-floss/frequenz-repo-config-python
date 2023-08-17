# Frequenz Repository Configuration Release Notes

## Summary

This version focus on some bug fixes and final polishing of v0.5.x.

## Upgrading

### Cookiecutter template

- If your replay file contains a `_extensions` key, you should remove it, as you most likely want to use the extensions declared by the repo-config cookiecutter template you are upgrading to, otherwise you could get errors about missing extensions.

- If your replay file contains a long `Introduction` key, you can replace it with an empty string (`""`), it doesn't need to have any particular content and it increases the size and noise in the replay file.

## New Features

### Cookiecutter template

- Generated project's dependencies were bumped.

- Move `TODO`s so they are in their own line.

  This makes it easier to upgrade projects to new templates, as removing whole lines is easier than having to edit them.

- Clean up `_extensions` from the generated replay file.

  It is not needed in the generated project, we always want to use the ones from the repo-config template.

  This should ease upgrading projects, making it less likely to have errors about missing extensions.

- Clean up the `Introduction` variable from the generated replay file.

  This is just a hack to be able to show a help about the template variables, keeping that text only increases the size and noise in the replay file.

- Add a `\n` to the end of the replay file.

  This is just to be nice to most editors and text files conventions, that likes it more if there is a `\n` at the end of the file.

- API: The common-api documentation now is cross-linked.

## Bug Fixes

### Cookiecutter template

- Properly label `conftest.py` files.
