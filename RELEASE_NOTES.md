# Frequenz Repository Configuration Release Notes

## Summary

This version accumulates a few improvements, and bumps the dependency of setuptools to use v75, which is compatible with PEP625, which is necessary to be able to keep uploading to PyPI, so you should upgrade to this version as soon as possible.

The migration script was also rewritten in Python, so it should be more compatible with different OSes.

## Upgrading

- The `frequenz.repo.config.github.abort()` function now takes most arguments as keyword-only arguments.
- The *Queue PRs for v0.x.x* GitHub ruleset was renamed to *Queue PRs for the default branch* and now targets the default branch. It also only have the merge queue restriction, all other restrictions were removed as they are already present in the *Protect version branches* ruleset. You might want to re-import this ruleset to your repositories.

## New Features

* Added a new GitHub branch ruleset for Rust projects.

### Cookiecutter template

* Group GitHub Actions dependabot updates.
* API projects don't include the `google-common-protos` dependency by default.
* API projects updated the `grpcio` dependency to `1.66.1`.
* API projects updated the `frequenz-api-common` dependency to `0.6`.
* Bump most of the dependencies.
* Change `edit_uri` default branch to v0.x.x in mkdocs.yml.
* Added a new default option `asyncio_default_fixture_loop_scope = "function"` for `pytest-asyncio` as not providing a value is deprecated.
* The migration script is now written in Python, so it should be (hopefully) more compatible with different OSes.
* Disable more `pylint` checks that are also checked by `mypy` to avoid false positives.
* Remove the redundant `--platform` from the testing dockerfile.

## Bug Fixes

* Sybil now parses the `__init__.py` file as well. Previously it was disabled due to an upstream bug.
