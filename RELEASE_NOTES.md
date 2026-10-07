# Frequenz Repository Configuration Release Notes

## Summary

This release documents deprecations with a `Deprecated:` admonition, generated automatically from the `typing_extensions.deprecated` decorator wherever there is one. It also bumps the minimum supported dependencies for protobuf, pytest and setuptools to exclude vulnerable versions.

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

- The `mypy` nox session now runs `mypy` once, without paths, so it checks the paths listed in the `files` option of the `tool.mypy` section in `pyproject.toml`, and it fails if that option is not set. Before, it ran `mypy` twice: once for the configured `packages` and once for the existing development paths (`tests`, `docs`, etc.). The migration script sets `files` for you; projects not using it need to replace `packages` with `mypy_path` and `files` themselves, see the `mypy` section of the [`frequenz.repo.config` documentation](https://frequenz-floss.github.io/frequenz-repo-config-python/latest/reference/frequenz/repo/config/) for an example.
- The `mypy` nox session now also warns about Python files in the repository (tracked by git, or untracked but not ignored) that `mypy` doesn't check, meaning not covered by `files` nor matched by `exclude`. In CI (when the `CI` environment variable is set to anything but an empty string, `0`, `false`, `no` or `off`, case-insensitive) this is an error instead, unless `Config.mypy_unchecked_files_error_in_ci` is set to `False`. Add those files to `files` if they should be type-checked, or to `exclude` if not.
- The `api` extra now requires `protobuf >= 7.35.1, < 9` and `setuptools >= 83.0.0, < 85`. The `extra-lint-examples` extra now requires `pytest >= 9.0.3, < 10`.

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSLf https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3 -I
```

But you might still need to adapt your code:

- Deprecations are now documented with a `Deprecated:` admonition, never `Warning: Deprecated`, and never with a custom title, since a title replaces the word "Deprecated" in the rendered output. The migration script rewrites a plain `Warning: Deprecated` into `Deprecated:` on its own, and reports the rest:

  - Symbols carrying both a `deprecated` decorator and a hand-written admonition, which would now be documented twice. Delete the hand-written one, moving into the decorator message anything it says that the message does not.
  - Variants such as `Note: Deprecated`, `Warning: Deprecation` or a custom title, where only a human can tell what was meant.

- Tests using a symbol deprecated by the project itself now fail. Stop using the deprecated symbol, or, when the use is deliberate, wrap it in [`pytest.deprecated_call()`](https://docs.pytest.org/en/stable/reference/reference.html#pytest.deprecated_call) (which is how a deprecation should be tested anyway) or mark the test with `@pytest.mark.filterwarnings("once::DeprecationWarning")`.

- The migration script can't add the filter if warnings are still configured through `addopts` instead of `filterwarnings`, or if the project's Python package can't be determined. It says so and prints what to add by hand.

- `mypy` now checks every package in the source directory, not only the one listed in `packages`, so it might report errors in code that was never type-checked before. The migration script only adds well-known locations to `files` (the source directory, `tests`/`pytests`, `examples`, `benchmarks`, `docs` and `noxfile.py`), and reports any other Python files as a manual step, so you can decide whether to add them to `files` or `exclude`. This includes paths your `noxfile.py` adds to the checked paths.

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

- mkdocstrings [relative cross-references](https://mkdocstrings.github.io/python/usage/configuration/docstrings/#relative_crossrefs) are now enabled, so docstrings can refer to objects relative to the one being documented, like `[.member]` or `[..sibling]`, instead of using the full path. The migration script enables them in existing projects too, unless `mkdocs.yml` already sets `relative_crossrefs`, in which case it is left alone.

- `mypy` is now configured with `mypy_path` and `files` instead of `packages`, so a plain `mypy` run checks the whole source directory plus tests, docs and `noxfile.py`, the same as the nox session.

- Generated projects now render deprecations as a `Deprecated:` admonition, styled like a warning but with its own colour and a grave stone icon.

  The [`griffe-warnings-deprecated`](https://mkdocstrings.github.io/griffe-warnings-deprecated/) extension builds that admonition from the message of a `typing_extensions.deprecated` decorator, so the text is written once and serves as both the runtime warning and the documentation. Where no decorator can reach, which is module-level aliases, individual function arguments, enum members and whole modules, the same admonition is written by hand.

- Generated projects now treat their own deprecations as errors in `pytest`, while deprecations coming from dependencies stay warnings, as they can't always be fixed right away:

  ```toml
  [tool.pytest.ini_options]
  filterwarnings = [
    "error",
    "once::DeprecationWarning",
    "once::PendingDeprecationWarning",
    'error:.*my\.own\.package\.[\w\.]+ (is|was) deprecated:DeprecationWarning',
  ]
  ```

  This is a heuristic: it only catches messages mentioning the fully qualified name of the deprecated symbol, as in `"my.own.package.mod.OldThing is deprecated since v1.2.0. Use [my.own.package.mod.NewThing][] instead."`, which is the style prescribed by the [deprecations guide](https://github.com/frequenz-floss/docs/blob/v0.x.x/python/deprecations.md).

  The entry goes after the `once::` ones, as later filters take precedence, and before any project-specific filter, which can then still override it.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- The mkdocstrings `paths` key in `mkdocs.yml` is back under `handlers.python`, where it belongs. Since v0.14.0 the template generated it directly under `handlers`, where mkdocstrings reads it as a handler name and aborts the build with `ModuleNotFoundError: No module named 'mkdocstrings_handlers.paths'`, so newly generated projects could not build their documentation. Existing projects are unaffected, as previous migration steps always moved the key to the correct place. The migration script now fixes both this location and the older `handlers.python.options` one.
- The instructions printed after generating a project, and the "Start a new project" guide, now use `v0.0-dev` as the initial `mike` version instead of `v0.1-dev`. A `v0.x.x` branch with no releases is published by the CI as `v0.0-dev`, so following the old instructions left a stale `v0.1-dev` version holding the `latest` alias.
