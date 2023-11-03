# Frequenz Repository Configuration Release Notes

## Summary

This release fixes a bug in `mike` version sorting.

## Upgrading

- `frequenz.repo.config.mkdocs.mike.`: The `sort_versions()` function now takes plain `str`s as arguments instead of `MikeVersionInfo` objects.

### Cookiecutter template

There is no need to regenerate any templates with this release.

## Bug Fixes

- CI / `mkdocs`: `mike` version sorting now properly sort pre-releases as older than stable releases for the same major and minor version.
