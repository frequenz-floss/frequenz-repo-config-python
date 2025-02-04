# Frequenz Repository Configuration Release Notes

## Summary

This release introduces a new MkDocs macros *pluglet* system that simplifies documentation setup and provides enhanced functionality for version information and code annotations. It also includes changes to how pytest warnings are handled in templates.

## Upgrading

- The `nox` default `pytest` session doesn't pass `-W=all -vv` to `pytest` anymore. You can use the `pyproject.toml` file to configure default options for `pytest`, for example:

    ```toml
    [tool.pytest.ini_options]
    addopts = "-W=all -Werror -Wdefault::DeprecationWarning -Wdefault::PendingDeprecationWarning -vv"
    ```

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.12/cookiecutter/migrate.py | python3
```

But you might still need to adapt your code:

- `pytest` now uses `-Werror` by default (but still treat deprecations as normal warnings), so if your tests run with warnings, they will now be turned to errors, and you'll need to fix them.

- Projects using `docs/_scripts/macros.py` with customized scripts can use the new provided utility functions. See the [`mkdocstrings_macros` documentation](https://frequenz-floss.github.io/frequenz-repo-config-python/v0.12/reference/frequenz/repo/config/mkdocs/mkdocstrings_macros/) for the new features and setup.

## New Features

- Two new modules were introduced to facilitate the configuration of `macros` for use within docstrings via `mkdocstrings`: [`mkdocstrings_macros`](https://frequenz-floss.github.io/frequenz-repo-config-python/v0.12/reference/frequenz/repo/config/mkdocs/mkdocstrings_macros/) and [`annotations`](https://frequenz-floss.github.io/frequenz-repo-config-python/v0.12/reference/frequenz/repo/config/mkdocs/annotations/).

### Cookiecutter template

- `pytest` now uses `-Werror -Wdefault::DeprecationWarning -Wdefault::PendingDeprecationWarning` by default. Deprecations are still treated as warnings, as when testing with the `pytest_min` session is normal to get deprecation warnings as we are using old versions of dependencies.

## Bug Fixes

### Cookiecutter template

- Fixed a compatibility issue in the macros doc script with `mkdocsstrings` 0.28.
