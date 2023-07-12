# Frequenz Repository Configuration Release Notes

## Summary

This release only ships fixes and improvements for Cookiecutter templates, it is recommended for existing projects to regenerate the templates.

## Upgrading

### Cookiecutter templates

* You might want to remove the `_output_dir` from the
  `.cookiecutter-replay.json` file, if there is one in your project.
* You will need to manually add `local_extensions.as_identifier` to the `_extensions` key in the `.cookiecutter-replay.json` file before running the replay.

## New Features

### Cookiecutter templates

* Add linting to the CI with `protolint` for API projects.
* Capitalize project name in title and expand shortened words.
* Add templates variables reference documentation in the genrated docs and when running Cookiecutter.
* Do some basic templates variables validation.

* `labeler` workflow configuration

  * Label `docs/*.py` as tooling.
  * Add example on how to exclude files.

* `pyproject.toml`

  * Bump SDK version to v0.22.0.
  * Disable `pylint`'s `unsubscriptable-object` check.
  * Add a few more default keywords.
  * Run `isort` in `benchmarks/` too

* `mkdocs`

  * Add more cross-reference inventories: `typing-extensions`, `frequenz-sdk`, `frequenz-channels`, `grpc`.
  * Add some extra markdown plugins: code annotations, copy button and line numbers, keys representation.
  * Be strict when building the docs (any warning will make the generation fail).

## Bug Fixes

### Cookiecutter templates

* Fix hardcoded MIT license headers. Now the user selected license is used instead.
* Properly handle project names with `-` and `_` in them.

* `pyproject.toml`

  * Add missing `repo-config` to `dev-mkdocs` dependencies.
  * Fix wrong optional dependency name for `dev` dependencies.
