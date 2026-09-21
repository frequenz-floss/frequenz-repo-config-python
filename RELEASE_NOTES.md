# Frequenz Repository Configuration Release Notes

## Summary

This release documents deprecations with a `Deprecated:` admonition, generated automatically from the `typing_extensions.deprecated` decorator wherever there is one.

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSLf https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3 -I
```

But you might still need to adapt your code:

- Deprecations are now documented with a `Deprecated:` admonition, never `Warning: Deprecated`, and never with a custom title, since a title replaces the word "Deprecated" in the rendered output. The migration script rewrites a plain `Warning: Deprecated` into `Deprecated:` on its own, and reports the rest:

  - Symbols carrying both a `deprecated` decorator and a hand-written admonition, which would now be documented twice. Delete the hand-written one, moving into the decorator message anything it says that the message does not.
  - Variants such as `Note: Deprecated`, `Warning: Deprecation` or a custom title, where only a human can tell what was meant.

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

- Generated projects now render deprecations as a `Deprecated:` admonition, styled like a warning but with its own colour and a grave stone icon.

  The [`griffe-warnings-deprecated`](https://mkdocstrings.github.io/griffe-warnings-deprecated/) extension builds that admonition from the message of a `typing_extensions.deprecated` decorator, so the text is written once and serves as both the runtime warning and the documentation. Where no decorator can reach, which is module-level aliases, individual function arguments, enum members and whole modules, the same admonition is written by hand.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- The mkdocstrings `paths` key in `mkdocs.yml` is back under `handlers.python`, where it belongs. Since v0.14.0 the template generated it directly under `handlers`, where mkdocstrings reads it as a handler name and aborts the build with `ModuleNotFoundError: No module named 'mkdocstrings_handlers.paths'`, so newly generated projects could not build their documentation. Existing projects are unaffected, as previous migration steps always moved the key to the correct place. The migration script now fixes both this location and the older `handlers.python.options` one.
- The instructions printed after generating a project, and the "Start a new project" guide, now use `v0.0-dev` as the initial `mike` version instead of `v0.1-dev`. A `v0.x.x` branch with no releases is published by the CI as `v0.0-dev`, so following the old instructions left a stale `v0.1-dev` version holding the `latest` alias.
