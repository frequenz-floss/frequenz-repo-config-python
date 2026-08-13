# Frequenz Repository Configuration Release Notes

## Summary

This release removes the now unnecessary DCO dummy workflow for the merge queue, enables debug mode for `pytest-asyncio` and exhaustive matching in `mypy`, makes `pytest` less verbose, improves the contributing guide's release steps, and brings the cookiecutter template up to date with the latest dependencies and GitHub Actions.

## Upgrading

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSLf https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3 -I
```

But you might still need to adapt your code:

- Generated API projects now build their Python bindings with `protobuf` 7.x (`grpcio-tools` 1.83.0 requires it), so the runtime requirement was raised to `protobuf >= 7.35.1, < 9`. Consumers of the generated bindings need to be able to install `protobuf` 7.x.

## New Features

### Cookiecutter template

- Generated `pyproject.toml` no longer sets `addopts = "-vv"` under `[tool.pytest.ini_options]` as this is too verbose for a default.
- Generated projects enable mypy's `exhaustive-match` error code.
- Generated non-API projects enable asyncio debug mode during tests to provide extra runtime checks.
- Removed the dummy DCO workflow for the merge queue, as the DCO GitHub App now runs on `merge_group` events. The `DCO` required status check in the "Protect version branches" ruleset is now pinned to the DCO GitHub App; the migration script removes the workflow and updates the ruleset (via the `gh` CLI) for existing repositories.

## Enhancements

- Improved the docstring documentation and cross-references across the `frequenz.repo.config` package.

### Cookiecutter template

- The `Releasing` section of `CONTRIBUTING.md` now covers the milestone handling, explains that the release notes are read from the `RELEASE_NOTES.md` committed at the tagged commit (so they can't be cleaned up after tagging), and that the tag signature is required by the *Protect released tags* ruleset, which also makes released tags immutable. The migration script updates existing repositories.
- All pinned dependencies were updated to their latest versions, most notably `setuptools` to 84.0.0, `mypy` to 2.3.0, `pytest` to 9.1.1, `pylint` to 4.0.7, `nox` to 2026.8.10, `pydoclint` to 0.9.1, `pytest-asyncio` to 1.4.0 and `flake8-datetimez` to 26.8.1 (its first release in almost 6 years).
- The `frequenz-sdk` requirement was bumped to 1.0.0rc2211 and, for API projects, `frequenz-api-common` to 0.8.11, `protobuf` to 7.35.1 and `grpcio`/`grpcio-tools` to 1.83.0.
- All GitHub Actions used by the generated workflows were updated to their latest releases, including the major bumps of `actions/checkout` to v7 and `actions/labeler` to v7 (no configuration changes are needed for either).
- API projects now run `protolint` 0.56.4 in CI (up from 0.53.0), which may report new issues in existing `.proto` files.

## Bug Fixes

- Fixed several typos and broken code examples in the docstrings.
- Fixed the building of distribution packages, which was failing with `setuptools-scm was unable to detect version`. When building a wheel from a source distribution there is no git repository to get the version from, so `setuptools-scm` 10.0.x reads it from `PKG-INFO` using an entry point provided by `vcs-versioning`, but it doesn't declare any upper bound for it. `vcs-versioning` 2.x dropped that entry point and moved the fallback to `setuptools-scm` itself, so builds started failing as soon as `vcs-versioning` 2.x was picked up. `setuptools-scm` was updated to 10.2.1, which provides the fallback again and bounds `vcs-versioning` to the 2.x series (backport from v0.18.2).

### Cookiecutter template

- The `frequenz-repo-config` version pinned by the template is bumped to the version being released again. It was left pointing at 0.17.0 in the v0.18.x series, so generated projects installed an outdated `frequenz-repo-config`.
