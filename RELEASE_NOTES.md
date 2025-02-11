# Frequenz Repository Configuration Release Notes

## Upgrading

Even if this is a patch release, it will require a dependency bump for `mkdocstrings-python` to v1.14.6 or newer, but since these are only dev dependencies and things will break if you update the dependencies anyway, it seems like a reasonable trade-off.

## Bug Fixes

- The new mkdocstrings-macros *pluglet* didn't work with the latest `mkdocstrings-python` version.
