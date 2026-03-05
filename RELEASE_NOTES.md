# Frequenz Repository Configuration Release Notes

> [!NOTE]
> This is a bugfix release for v0.15.0. This release was never published to PyPI, so we keep the entire release notes for v0.15.0 here (updated to the new changes) to make it easier for users to upgrade from v0.14.0 to v0.15.x.
>
> The only change with respect to v0.15.0 is using the appropriate job runner for the `publish-to-pypi` job in `ci.yaml`. v0.15.0 updated it to `ubuntu-slim` but that didn't work because it requires Docker, and it is not installed on the `ubuntu-slim` runner.

## Summary

This release reduces CI cost by moving lightweight GitHub Actions jobs to the new `ubuntu-slim` runner, fixes Dependabot auto-merge/merge-queue issues by switching to a GitHub App installation token, and introduces an automated repo-config migration workflow (including updating existing repos' version-branch protection defaults).

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

### Cookiecutter template

All upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.15.0/cookiecutter/migrate.py | python3
```

But you might still need to adapt your code:

<!-- Here upgrade steps for cookiecutter specifically -->

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

### Cookiecutter template

- Migrated lightweight workflow jobs to use the new `ubuntu-slim` runner for cost savings.
  The following jobs now use `ubuntu-slim`:
  - `ci.yaml`: `protolint`, `nox-all`, `test-installation-all`, `create-github-release`
  - `ci-pr.yaml`: `protolint`
  - `auto-dependabot.yaml`: `auto-merge`
  - `release-notes-check.yml`: `check-release-notes`
  - `dco-merge-queue.yml`: `DCO`
  - `labeler.yml`: `Label`

- Migrated the `publish-to-pypi` job in `ci.yaml` from `ubuntu-latest` to `ubuntu-24.04` to get reproducible builds.

- Added the [`flake8-datetimez`](https://github.com/pjknkda/flake8-datetimez) plugin to the `flake8` session. This plugin prevents accidental use of naive `datetime` objects by flagging calls that create or return datetimes without timezone information.

- The CI workflow now uses a simpler matrix.

- Added `repo-config-migration.yaml` workflow that automatically runs the migration script, commits changes, posts results, and auto-approves/merges only when no migration commit is created.

  The workflow handles multi-version jumps by running each intermediate migration in sequence. The migration script output is posted as a PR comment and in the job summary. PRs with migration commits stay open for manual approval and merge. PRs that need manual intervention fail the job until a human completes the steps and signals resolution by removing the `tool:repo-config:migration:intervention-pending` label or adding the `tool:repo-config:migration:intervention-done` label.

- The `auto-dependabot.yaml` workflow now skips repo-config group PRs, which are handled by the new migration workflow instead.

- Updated the default "Protect version branches" ruleset to require the new `Migrate Repo Config` status check, which is added by the migration workflow to PRs that need manual intervention. This prevents merging PRs that require manual migration steps until those steps are completed and the check passes. Also removed the required code-owner approval and automatic Copilot review request.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

### Cookiecutter template

- Switched `project.license` to SPDX expressions and added `project.license-files`. This removes deprecated setuptools license metadata and avoids build warnings.

- Fixed auto-dependabot workflow failing to trigger merge queue CI or complete auto-merge. The workflow now uses a GitHub App installation token (via `actions/create-github-app-token`) instead of `GITHUB_TOKEN`, which was suppressing subsequent workflow runs by design. Workflow permissions have been reduced to the minimum needed for the workflow (`contents: read` and `pull-requests: write`).

- Fix dependabot group patterns for repo-config and mkdocstrings.
