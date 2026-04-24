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

- The cookiecutter now asks whether a repository is private, defaults that answer from the selected license, and uses it to toggle private-repository workflow behavior, public publishing jobs, and the link to GitHub Discussions in the issue template chooser.
- All dependencies have been updated in the templates.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- The unused cross-arch QEMU-based testing infrastructure has been removed. The `.github/containers/nox-cross-arch/` and `.github/containers/test-installation/` directories, as well as the "Cross-Arch Testing" section in `CONTRIBUTING.md`.
- Private repositories now are generated with credentials uncommented and the publishing workflows disabled.
- The issue template chooser (`config.yml`) no longer includes the `contact_links` section for private repositories, since GitHub Discussions are typically disabled for them.
