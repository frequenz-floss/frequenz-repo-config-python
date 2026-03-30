# Frequenz Repository Configuration Release Notes

## Summary

This release improves workflows security, adds a black migration workflow, and fixes failed migrations from version v0.16.0.

## Upgrading

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSLf https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3 -I
```

But you might still need to adapt your code:

## New Features

### Cookiecutter template

- Add a `black-migration.yaml` workflow that automatically reformats code when Dependabot upgrades `black`.

## Bug Fixes

### Cookiecutter template

- Fix migration of CI workflow matrices that used `arch`/`os` dimensions with values different from the default template. The v0.16.0 migration relied on exact string matching, so projects with customized matrix items (for example `arch: [amd64]`, `os: [ubuntu-24.04]`) could be left only partially migrated. The new migration step rebuilds the `platform` entries from the existing `arch`/`os` values and only rewrites `runs-on` when it still points to the old matrix keys.
- Improve workflows security: tighten permissions, avoid potential shell injection, run Python in isolated mode, pin all dependencies using the SHA hash.
- The unused cross-arch QEMU-based testing infrastructure has been removed. The `.github/containers/nox-cross-arch/` and `.github/containers/test-installation/` directories, as well as the "Cross-Arch Testing" section in `CONTRIBUTING.md`.
