# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSLf https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3 -I
```

But you might still need to adapt your code:

<!-- Here upgrade steps for cookiecutter specifically -->

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

<!-- Here new features for cookiecutter specifically -->

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- Fix migration of CI workflow matrices that used `arch`/`os` dimensions with values different from the default template. The v0.16.0 migration relied on exact string matching, so projects with customized matrix items (for example `arch: [amd64]`, `os: [ubuntu-24.04]`) could be left only partially migrated. The new migration step rebuilds the `platform` entries from the existing `arch`/`os` values and only rewrites `runs-on` when it still points to the old matrix keys.
