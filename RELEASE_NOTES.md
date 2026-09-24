# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

- The `mypy` nox session now runs `mypy` once, without paths, so it checks the paths listed in the `files` option of the `tool.mypy` section in `pyproject.toml`, and it fails if that option is not set. Before, it ran `mypy` twice: once for the configured `packages` and once for the existing development paths (`tests`, `docs`, etc.). The migration script sets `files` for you; projects not using it need to replace `packages` with `mypy_path` and `files` themselves, see the `mypy` section of the [`frequenz.repo.config` documentation](https://frequenz-floss.github.io/frequenz-repo-config-python/latest/reference/frequenz/repo/config/) for an example.
- The `mypy` nox session now also warns about Python files in the repository (tracked by git, or untracked but not ignored) that `mypy` doesn't check, meaning not covered by `files` nor matched by `exclude`. In CI (when the `CI` environment variable is set to anything but an empty string, `0`, `false`, `no` or `off`, case-insensitive) this is an error instead, unless `Config.mypy_unchecked_files_error_in_ci` is set to `False`. Add those files to `files` if they should be type-checked, or to `exclude` if not.

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSLf https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3 -I
```

But you might still need to adapt your code:

<!-- Here upgrade steps for cookiecutter specifically -->

- `mypy` now checks every package in the source directory, not only the one listed in `packages`, so it might report errors in code that was never type-checked before. The migration script only adds well-known locations to `files` (the source directory, `tests`/`pytests`, `examples`, `benchmarks`, `docs` and `noxfile.py`), and reports any other Python files as a manual step, so you can decide whether to add them to `files` or `exclude`. This includes paths your `noxfile.py` adds to the checked paths.

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

- mkdocstrings [relative cross-references](https://mkdocstrings.github.io/python/usage/configuration/docstrings/#relative_crossrefs) are now enabled, so docstrings can refer to objects relative to the one being documented, like `[.member]` or `[..sibling]`, instead of using the full path. The migration script enables them in existing projects too, unless `mkdocs.yml` already sets `relative_crossrefs`, in which case it is left alone.

- `mypy` is now configured with `mypy_path` and `files` instead of `packages`, so a plain `mypy` run checks the whole source directory plus tests, docs and `noxfile.py`, the same as the nox session.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- The mkdocstrings `paths` key in `mkdocs.yml` is back under `handlers.python`, where it belongs. Since v0.14.0 the template generated it directly under `handlers`, where mkdocstrings reads it as a handler name and aborts the build with `ModuleNotFoundError: No module named 'mkdocstrings_handlers.paths'`, so newly generated projects could not build their documentation. Existing projects are unaffected, as previous migration steps always moved the key to the correct place. The migration script now fixes both this location and the older `handlers.python.options` one.
- The instructions printed after generating a project, and the "Start a new project" guide, now use `v0.0-dev` as the initial `mike` version instead of `v0.1-dev`. A `v0.x.x` branch with no releases is published by the CI as `v0.0-dev`, so following the old instructions left a stale `v0.1-dev` version holding the `latest` alias.
