#!/usr/bin/env python3
# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Script to migrate existing projects to new versions of the cookiecutter template.

This script migrates existing projects to new versions of the cookiecutter
template, removing the need to completely regenerate the project from
scratch.

To run it, the simplest way is to fetch it from GitHub and run it directly:

    curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3

Make sure to replace the `<tag>` to the version you want to migrate to in the URL.

For jumping multiple versions you should run the script multiple times, once
for each version.

And remember to follow any manual instructions for each run.
"""  # noqa: E501

# pylint: disable=too-many-lines

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, SupportsIndex

_manual_steps: list[str] = []  # pylint: disable=invalid-name


def main() -> None:
    """Run the migration steps."""
    # Add a separation line like this one after each migration step.
    print("=" * 72)
    print("Migrating workflows to use ubuntu-slim runner for lightweight jobs...")
    migrate_to_ubuntu_slim()
    print("=" * 72)
    print("Migrating publish-to-pypi workflow runner to ubuntu-24.04...")
    migrate_publish_to_pypi_runner()
    print("=" * 72)
    print("Migrating pyproject license metadata to SPDX format...")
    migrate_pyproject_license()
    print("=" * 72)
    print("Adding flake8-datetimez plugin to dev-flake8 dependencies...")
    migrate_add_flake8_datetimez()
    print("=" * 72)
    print("Fixing dependabot repo-config and mkdocstrings patterns...")
    migrate_dependabot_patterns()
    print("=" * 72)
    print("Migrating auto-dependabot workflow to use GitHub App token...")
    migrate_auto_dependabot_token()
    print("=" * 72)
    print("Migrating the CI workflows to use a platform matrix...")
    migrate_platform_matrix()
    print("=" * 72)
    print("Installing repo-config migration workflow...")
    migrate_repo_config_workflow()
    print("=" * 72)
    print("Updating 'Protect version branches' GitHub ruleset...")
    migrate_protect_version_branches_ruleset()
    print("=" * 72)
    print()

    if _manual_steps:
        print(
            "\033[5;33m⚠️⚠️⚠️\033[0;33m Remember to check the manual steps: \033[5;33m⚠️⚠️⚠️\033[0m"
        )
        for n, step in enumerate(_manual_steps, start=1):
            print(f"\033[5;33m⚠️⚠️⚠️   \033[0;33m{n}. {step}\033[0m")
        print()

        print(
            "\033[5;31m❌\033[0;31m Migration script finished but requires manual "
            "intervention \033[5;31m❌\033[0m"
        )
        print()

        sys.exit(len(_manual_steps))

    print("\033[0;32m       ✅ Migration script finished successfully ✅\033[0m")
    print()


def migrate_to_ubuntu_slim() -> None:
    """Migrate workflow files to use ubuntu-slim runner for lightweight jobs.

    This updates several workflow files to use the new cost-effective ubuntu-slim
    runner for jobs that are lightweight (e.g., labeling, release notes checks,
    simple API calls).
    """
    workflows_dir = Path(".github") / "workflows"
    project_type = read_project_type()
    include_protolint = project_type == "api"
    if project_type is None:
        include_protolint = True
        manual_step(
            "Unable to detect the cookiecutter project type from "
            ".cookiecutter-replay.json; protolint migrations will run anyway. "
            "Please verify any protolint jobs and keep them only if this is an api "
            "project."
        )

    migrations = {
        "ci.yaml": [
            {
                "job": "nox-all",
                "old": (
                    "    if: always() && needs.nox.result != 'skipped'\n"
                    "    runs-on: ubuntu-24.04"
                ),
                "new": (
                    "    if: always() && needs.nox.result != 'skipped'\n"
                    "    runs-on: ubuntu-slim"
                ),
            },
            {
                "job": "test-installation-all",
                "old": (
                    "    if: always() && needs.test-installation.result != 'skipped'\n"
                    "    runs-on: ubuntu-24.04"
                ),
                "new": (
                    "    if: always() && needs.test-installation.result != 'skipped'\n"
                    "    runs-on: ubuntu-slim"
                ),
            },
            {
                "job": "create-github-release",
                "old": "      discussions: write\n    runs-on: ubuntu-24.04",
                "new": "      discussions: write\n    runs-on: ubuntu-slim",
            },
        ],
        "release-notes-check.yml": [
            {
                "job": "check-release-notes",
                "old": (
                    "  check-release-notes:\n"
                    "    name: Check release notes are updated\n"
                    "    runs-on: ubuntu-latest"
                ),
                "new": (
                    "  check-release-notes:\n"
                    "    name: Check release notes are updated\n"
                    "    runs-on: ubuntu-slim"
                ),
            }
        ],
        "dco-merge-queue.yml": [
            {
                "job": "DCO",
                "old": "jobs:\n  DCO:\n    runs-on: ubuntu-latest",
                "new": "jobs:\n  DCO:\n    runs-on: ubuntu-slim",
            }
        ],
        "labeler.yml": [
            {
                "job": "Label",
                "old": (
                    "  Label:\n"
                    "    permissions:\n"
                    "      contents: read\n"
                    "      pull-requests: write\n"
                    "    runs-on: ubuntu-latest"
                ),
                "new": (
                    "  Label:\n"
                    "    permissions:\n"
                    "      contents: read\n"
                    "      pull-requests: write\n"
                    "    runs-on: ubuntu-slim"
                ),
            }
        ],
    }
    if include_protolint:
        protolint_rule = {
            "job": "protolint",
            "old": (
                "  protolint:\n"
                "    name: Check proto files with protolint\n"
                "    runs-on: ubuntu-24.04"
            ),
            "new": (
                "  protolint:\n"
                "    name: Check proto files with protolint\n"
                "    runs-on: ubuntu-slim"
            ),
        }
        migrations.setdefault("ci-pr.yaml", []).append(protolint_rule)
        migrations.setdefault("ci.yaml", []).append(protolint_rule)

    for filename, rules in migrations.items():
        filepath = workflows_dir / filename
        if not filepath.exists():
            print(f"  Skipping {filepath} (file not found)")
            continue

        for rule in rules:
            job = rule["job"]
            old = rule["old"]
            new = rule["new"]
            try:
                content = filepath.read_text(encoding="utf-8")
            except FileNotFoundError:
                continue

            if old in content:
                replace_file_contents_atomically(filepath, old, new)
                print(f"  Updated {filepath}: migrated job {job} to ubuntu-slim")
                continue

            if new in content:
                print(f"  Skipped {filepath}: already uses ubuntu-slim for job {job}")
                continue

            manual_step(
                f"  Pattern not found in {filepath}: please switch job {job} to use "
                "`runs-on: ubuntu-slim` where appropriate."
            )


def migrate_publish_to_pypi_runner() -> None:
    """Migrate the publish-to-pypi CI job runner to ubuntu-24.04."""
    github_org = read_cookiecutter_github_org()
    if github_org != "frequenz-floss":
        print("  Skipping .github/workflows/ci.yaml (publish-to-pypi not expected)")
        return

    filepath = Path(".github") / "workflows" / "ci.yaml"
    if not filepath.exists():
        print(f"  Skipping {filepath} (file not found)")
        return

    old = '    needs: ["create-github-release"]\n    runs-on: ubuntu-latest'
    new = '    needs: ["create-github-release"]\n    runs-on: ubuntu-24.04'
    content = filepath.read_text(encoding="utf-8")

    if old in content:
        replace_file_contents_atomically(filepath, old, new)
        print(f"  Updated {filepath}: migrated runner for job publish-to-pypi")
        return

    if new in content:
        print(
            f"  Skipped {filepath}: runner already up to date for job publish-to-pypi"
        )
        return

    manual_step(
        f"  Pattern not found in {filepath}: please switch the runner for job "
        "publish-to-pypi according to the latest template."
    )


def migrate_pyproject_license() -> None:  # pylint: disable=too-many-branches
    """Migrate pyproject license metadata to SPDX expressions."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("  Skipping pyproject.toml (file not found)")
        return

    content = pyproject_path.read_text(encoding="utf-8")
    new_content = content
    updated = False

    license_expression = None
    for old_license, new_license in (
        ("MIT", "MIT"),
        ("Proprietary", "LicenseRef-Proprietary"),
        ("Propietary", "LicenseRef-Proprietary"),
    ):
        old_line = f'license = {{ text = "{old_license}" }}'
        if old_line in new_content:
            new_content = new_content.replace(old_line, f'license = "{new_license}"', 1)
            license_expression = new_license
            updated = True
            break

    if license_expression is None:
        for existing_license in ("MIT", "LicenseRef-Proprietary"):
            if f'license = "{existing_license}"' in new_content:
                license_expression = existing_license
                break

    if license_expression is None:
        cookiecutter_license = read_cookiecutter_license()
        if cookiecutter_license == "MIT":
            license_expression = "MIT"
        elif cookiecutter_license == "Proprietary":
            license_expression = "LicenseRef-Proprietary"

    if license_expression is None:
        manual_step(
            "Unable to detect project license in pyproject.toml. Please set "
            "`project.license` to a SPDX expression and add "
            '`project.license-files = ["LICENSE"]`.'
        )
        return

    license_line = f'license = "{license_expression}"'
    if "license-files" not in new_content and license_line in new_content:
        new_content = new_content.replace(
            license_line, f'{license_line}\nlicense-files = ["LICENSE"]', 1
        )
        updated = True

    for classifier in (
        "License :: OSI Approved :: MIT License",
        "License :: Other/Proprietary License",
    ):
        classifier_line = f'  "{classifier}",\n'
        if classifier_line in new_content:
            new_content = new_content.replace(classifier_line, "", 1)
            updated = True

    setuptools_version = parse_setuptools_version(new_content)
    if setuptools_version is not None and setuptools_version < 77:
        new_content, replaced = replace_setuptools_pin(new_content, "80.9.0")
        if replaced:
            updated = True

    if not updated or new_content == content:
        print("  Skipped pyproject.toml (already up to date)")
        return

    replace_file_contents_atomically(pyproject_path, content, new_content, count=1)
    print("  Updated pyproject.toml: migrated license metadata")


def migrate_add_flake8_datetimez() -> None:
    """Add the flake8-datetimez plugin to dev-flake8 dependencies."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("  Skipping pyproject.toml (file not found)")
        return

    content = pyproject_path.read_text(encoding="utf-8")

    if "flake8-datetimez" in content:
        print("  Skipped pyproject.toml (flake8-datetimez already present)")
        return

    # Look for a pinned flake8 dependency line (e.g. "flake8 == 7.3.0") and
    # insert flake8-datetimez right after it.
    match = re.search(r'(  "flake8\s*==.*",?\n)', content)
    if not match:
        manual_step(
            "Could not find a flake8 pin in pyproject.toml. "
            'Please add `"flake8-datetimez == 20.10.0"` to the '
            "`dev-flake8` optional dependencies."
        )
        return

    flake8_line = match.group(1)
    new_content = content.replace(
        flake8_line,
        flake8_line + '  "flake8-datetimez == 20.10.0",\n',
        1,
    )
    replace_file_contents_atomically(pyproject_path, content, new_content, count=1)
    print("  Updated pyproject.toml: added flake8-datetimez plugin")


def migrate_dependabot_patterns() -> None:
    """Fix dependabot repo-config and mkdocstrings dependency patterns.

    Dependabot wildcards don't work when ``[]`` is involved in optional
    dependency specifiers, so we need to list them explicitly in the
    include/exclude patterns.

    This replaces ``frequenz-repo-config*`` with explicit entries for the
    base package, the project-type extra, and the ``extra-lint-examples``
    extra, and adds ``mkdocstrings[python]`` alongside ``mkdocstrings*``.
    """
    filepath = Path(".github") / "dependabot.yml"
    if not filepath.exists():
        manual_step(
            f"Unable to find {filepath}. Please update your dependabot config "
            "manually by replacing any `frequenz-repo-config*` patterns with explicit "
            "entries for `frequenz-repo-config`, `frequenz-repo-config[<your-type>]`, and "
            "`frequenz-repo-config[extra-lint-examples]`, and add `mkdocstrings[python]` "
            "to the patterns for the `mkdocstrings` group if it is missing."
        )
        return

    content = filepath.read_text(encoding="utf-8")
    new_content = content
    updated = False

    project_type = read_project_type()
    if project_type is None:
        manual_step(
            "Unable to detect the cookiecutter project type from "
            ".cookiecutter-replay.json; cannot determine the correct "
            "frequenz-repo-config optional dependency for dependabot.yml. "
            "Please replace any `frequenz-repo-config*` patterns with explicit "
            "entries for `frequenz-repo-config`, "
            "`frequenz-repo-config[<your-type>]`, and "
            "`frequenz-repo-config[extra-lint-examples]`."
        )
        return

    # Replace frequenz-repo-config* with explicit entries (appears in both
    # exclude-patterns and repo-config group patterns).
    old_repo_config = '          - "frequenz-repo-config*"\n'
    new_repo_config = (
        '          - "frequenz-repo-config"\n'
        f'          - "frequenz-repo-config[{project_type}]"\n'
        '          - "frequenz-repo-config[extra-lint-examples]"\n'
    )
    if old_repo_config in new_content:
        new_content = new_content.replace(old_repo_config, new_repo_config)
        updated = True
    elif f'"frequenz-repo-config[{project_type}]"' in new_content:
        print(f"  Skipped {filepath}: repo-config patterns already updated")
    else:
        manual_step(
            f"Could not find `frequenz-repo-config*` pattern in {filepath}. "
            "Please replace it with explicit entries for "
            "`frequenz-repo-config`, "
            f"`frequenz-repo-config[{project_type}]`, and "
            "`frequenz-repo-config[extra-lint-examples]`."
        )

    # Add mkdocstrings[python] after mkdocstrings* (appears in both
    # exclude-patterns and mkdocstrings group patterns).
    old_mkdocstrings = '          - "mkdocstrings*"\n'
    new_mkdocstrings = (
        '          - "mkdocstrings*"\n          - "mkdocstrings[python]"\n'
    )
    if old_mkdocstrings in new_content and '"mkdocstrings[python]"' not in new_content:
        new_content = new_content.replace(old_mkdocstrings, new_mkdocstrings)
        updated = True
    elif '"mkdocstrings[python]"' in new_content:
        print(f"  Skipped {filepath}: mkdocstrings patterns already updated")
    else:
        manual_step(
            f"Could not find `mkdocstrings*` pattern in {filepath}. "
            'Please add `"mkdocstrings[python]"` alongside `"mkdocstrings*"` '
            "in both the exclude-patterns and the mkdocstrings group."
        )

    if not updated or new_content == content:
        print(f"  Skipped {filepath} (already up to date)")
        return

    replace_file_contents_atomically(filepath, content, new_content, count=1)
    print(f"  Updated {filepath}: fixed repo-config and mkdocstrings patterns")


def migrate_auto_dependabot_token() -> None:
    """Migrate auto-dependabot workflow to use a GitHub App installation token.

    This replaces the GITHUB_TOKEN with a GitHub App installation token to
    ensure that auto-merge and merge queue events are properly triggered.
    Using GITHUB_TOKEN suppresses subsequent workflow runs (by design), which
    prevents merge queue CI from running and can cause auto-merge to silently
    fail.

    This migration intentionally overwrites `.github/workflows/auto-dependabot.yaml`
    with the template version, as the workflow is small and user customizations
    are not supported.
    """
    filepath = Path(".github") / "workflows" / "auto-dependabot.yaml"
    # This is separated only to avoid flake8 errors about line length
    dependabot_auto_approve_version = (
        "e943399cc9d76fbb6d7faae446cd57301d110165 # v1.5.0"
    )
    desired_content = (
        r"""name: Auto-merge Dependabot PR

on:
  # XXX: !!! SECURITY WARNING !!!
  # pull_request_target has write access to the repo, and can read secrets. We
  # need to audit any external actions executed in this workflow and make sure no
  # checked out code is run (not even installing dependencies, as installing
  # dependencies usually can execute pre/post-install scripts). We should also
  # only use hashes to pick the action to execute (instead of tags or branches).
  # For more details read:
  # https://securitylab.github.com/research/github-actions-preventing-pwn-requests/
  pull_request_target:

permissions:
  contents: read
  pull-requests: write

jobs:
  auto-merge:
    name: Auto-merge Dependabot PR
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-slim
    steps:
      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf # v2.2.1
        with:
          app-id: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_ID }}
          private-key: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY }}

      - name: Auto-merge Dependabot PR
        uses: frequenz-floss/dependabot-auto-approve@"""
        + dependabot_auto_approve_version
        + r"""
        with:
          github-token: ${{ steps.app-token.outputs.token }}
          dependency-type: 'all'
          auto-merge: 'true'
          merge-method: 'merge'
          add-label: 'tool:auto-merged'
"""
    )

    if filepath.exists():
        content = filepath.read_text(encoding="utf-8").replace("\r\n", "\n")
        if content == desired_content:
            print(f"  Skipped {filepath}: already up to date")
            return

        print(
            f"  Replacing {filepath} with updated workflow (overwriting any local changes)"
        )
        replace_file_atomically(filepath, desired_content)
        return

    filepath.parent.mkdir(parents=True, exist_ok=True)
    replace_file_atomically(filepath, desired_content)
    print(f"  Added {filepath}: installed updated workflow")


def migrate_repo_config_workflow() -> None:
    """Install the repo-config migration workflow and update auto-dependabot.

    This installs the ``repo-config-migration.yaml`` workflow that uses the
    ``frequenz-floss/gh-action-dependabot-migrate`` action.  It also
    updates ``auto-dependabot.yaml`` to skip repo-config group PRs (which
    are handled by the migration workflow instead).

    The workflow file is created from scratch (overwriting any previous
    version) to ensure it stays in sync with the latest template.
    """
    workflows_dir = Path(".github") / "workflows"
    if not workflows_dir.is_dir():
        print("  Skipping (no .github/workflows directory found)")
        return

    # ── Install repo-config-migration.yaml ────────────────────────────
    migration_wf = workflows_dir / "repo-config-migration.yaml"
    desired_content = (
        r"""# Automatic repo-config migrations for Dependabot PRs
#
# The companion auto-dependabot workflow skips repo-config group PRs so
# they're handled exclusively by the migration workflow.
#
# XXX: !!! SECURITY WARNING !!!
# pull_request_target has write access to the repo, and can read secrets.
# This is required because Dependabot PRs are treated as fork PRs: the
# GITHUB_TOKEN is read-only and secrets are unavailable with a plain
# pull_request trigger.  The action mitigates the risk by:
#   - Never executing code from the PR (migrate.py is fetched from an
#     upstream tag, not from the checked-out branch).
#   - Gating migration steps on github.actor == 'dependabot[bot]'.
#   - Running checkout with persist-credentials: false and isolating
#     push credentials from the migration script environment.
# For more details read:
# https://securitylab.github.com/research/github-actions-preventing-pwn-requests/

name: Repo Config Migration

on:
  pull_request_target:
    types: [opened, synchronize, reopened, labeled, unlabeled]

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  repo-config-migration:
    name: Migrate Repo Config
    if: contains(github.event.pull_request.title, 'the repo-config group')
    runs-on: ubuntu-24.04
    steps:
      - name: Generate token
        id: create-app-token
        uses: actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf # v2.2.1
        with:
          app-id: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_ID }}
          private-key: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY }}
      - name: Migrate
        uses: frequenz-floss/gh-action-dependabot-migrate@07dc7e74726498c50726a80cc2167a04d896508f # v1.0.0
        with:
          script-url-template: >-
            https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/{version}/cookiecutter/migrate.py"""  # noqa: E501
        r"""
          token: ${{ steps.create-app-token.outputs.token }}
          migration-token: ${{ secrets.REPO_CONFIG_MIGRATION_TOKEN }}
          sign-commits: "true"
          auto-merged-label: "tool:auto-merged"
          migrated-label: "tool:repo-config:migration:executed"
          intervention-pending-label: "tool:repo-config:migration:intervention-pending"
          intervention-done-label: "tool:repo-config:migration:intervention-done"
"""
    )

    if migration_wf.exists():
        content = migration_wf.read_text(encoding="utf-8").replace("\r\n", "\n")
        if content == desired_content:
            print(f"  Skipped {migration_wf}: already up to date")
        else:
            print(
                f"  Replacing {migration_wf} with updated workflow"
                " (overwriting any local changes)"
            )
            replace_file_atomically(migration_wf, desired_content)
    else:
        workflows_dir.mkdir(parents=True, exist_ok=True)
        replace_file_atomically(migration_wf, desired_content)
        print(f"  Installed {migration_wf}")

    # ── Update auto-dependabot.yaml ───────────────────────────────────
    #
    # Add a condition to skip repo-config group PRs, which are now
    # handled by the migration workflow instead.
    auto_dep = workflows_dir / "auto-dependabot.yaml"
    if not auto_dep.exists():
        print(f"  Skipping {auto_dep} (file not found)")
        return

    dep_content = auto_dep.read_text(encoding="utf-8")

    # Already has the exclusion condition.
    if "the repo-config group" in dep_content:
        print(f"  Skipped {auto_dep} (already excludes repo-config group)")
        return

    # Match both multi-line and single-line `if` formats, with any runner.
    old_patterns = [
        # Multi-line if (e.g. from a previous migration that used ubuntu-slim)
        ("    if: github.actor == 'dependabot[bot]'\n    runs-on: ubuntu-slim"),
        ("    if: github.actor == 'dependabot[bot]'\n    runs-on: ubuntu-latest"),
        ("    if: github.actor == 'dependabot[bot]'\n    runs-on: ubuntu-24.04"),
    ]

    new_template = (
        "    if: >\n"
        "      github.actor == 'dependabot[bot]' &&\n"
        "      !contains(github.event.pull_request.title, 'the repo-config group')\n"
        "    runs-on: {runner}"
    )

    for old_pattern in old_patterns:
        if old_pattern in dep_content:
            # Extract the runner from the old pattern.
            runner = old_pattern.rsplit("runs-on: ", 1)[1]
            new_block = new_template.format(runner=runner)
            replace_file_contents_atomically(auto_dep, old_pattern, new_block)
            print(f"  Updated {auto_dep}: added repo-config group exclusion")
            return

    # If we didn't match any known pattern, flag a manual step.
    manual_step(
        f"Could not update {auto_dep} automatically. Please add a condition "
        "to skip repo-config group PRs: "
        "`!contains(github.event.pull_request.title, 'the repo-config group')`"
    )


def migrate_protect_version_branches_ruleset() -> None:
    """Update the 'Protect version branches' GitHub ruleset.

    Uses the GitHub API (via ``gh`` CLI) to check whether the
    'Protect version branches' ruleset on the current repository is aligned
    with the current template.  Recent template changes include:

    * Setting ``require_code_owner_review`` to ``false``.
    * Adding an (empty) ``required_reviewers`` list.
    * Removing the ``automatic_copilot_code_review_enabled`` setting.
    * Adding ``Migrate Repo Config`` to the required status checks.
    * Setting the ``OrganizationAdmin`` bypass-actor ``actor_id`` to
      ``null``.

    If the ruleset is already aligned, prints an informational message.
    If it needs updating, applies the changes via the API without removing
    any existing required status checks.
    If the ruleset is not found at all, issues a manual-step message that
    points the user to the docs.
    """
    rule_name = "Protect version branches"
    docs_url = (
        "https://frequenz-floss.github.io/frequenz-repo-config-python/"
        "user-guide/start-a-new-project/configure-github/#rulesets"
    )

    # Build a link to the repo's ruleset settings for manual-step messages.
    ruleset_url = get_ruleset_settings_url() or docs_url

    # ── Fetch ruleset details ────────────────────────────────────────
    ruleset = get_ruleset(rule_name)
    if ruleset is None:
        manual_step(
            f"The '{rule_name}' GitHub ruleset was not found (or the gh CLI "
            "is not available / the API call failed). "
            "Please check whether it should exist for this repository. "
            f"If it should, import it following the instructions at: {docs_url}"
        )
        return

    ruleset_id = ruleset.get("id")
    if not isinstance(ruleset_id, int):
        manual_step(
            f"Failed to determine the '{rule_name}' ruleset ID from the "
            f"GitHub API response. Please update it manually at: {ruleset_url}"
        )
        return

    # ── Detect and apply changes in-memory ───────────────────────────────
    changes: list[str] = []

    for rule in ruleset.get("rules", []):
        if rule.get("type") == "pull_request":
            params = rule.setdefault("parameters", {})
            if params.get("require_code_owner_review") is True:
                params["require_code_owner_review"] = False
                changes.append("set require_code_owner_review=false")
            if params.pop("automatic_copilot_code_review_enabled", None) is not None:
                changes.append("remove automatic_copilot_code_review_enabled")

        elif rule.get("type") == "required_status_checks":
            params = rule.setdefault("parameters", {})
            checks = params.setdefault("required_status_checks", [])
            if not any(c.get("context") == "Migrate Repo Config" for c in checks):
                checks.append(
                    {"context": "Migrate Repo Config", "integration_id": 15368}
                )
                changes.append("add 'Migrate Repo Config' status check")

    if not changes:
        print(f"  Ruleset '{rule_name}' is already up to date")
        return

    # ── Push the update ───────────────────────────────────────────────────
    if not update_ruleset(ruleset_id, ruleset):
        manual_step(
            f"Failed to update the '{rule_name}' ruleset via the GitHub API. "
            f"Please apply the following changes manually at {ruleset_url}: "
            + "; ".join(changes)
        )
        return

    print(f"  Updated ruleset '{rule_name}': " + ", ".join(changes))


def find_ruleset(name: str) -> dict[str, Any] | None:
    """Find a repository ruleset by name using the GitHub API.

    Args:
        name: The name of the ruleset to search for.

    Returns:
        The ruleset summary dict (id, name, …) if found, or ``None`` if not
        found or if the API call failed (a diagnostic is printed in the latter
        case).
    """
    try:
        stdout = subprocess.check_output(
            ["gh", "api", "repos/:owner/:repo/rulesets"],
            text=True,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        print("  gh CLI not found; cannot query rulesets via the GitHub API.")
        return None
    except subprocess.CalledProcessError as exc:
        print(f"  Failed to list rulesets: {exc.stderr.strip()}")
        return None

    rulesets: list[dict[str, Any]] = json.loads(stdout)
    return next((r for r in rulesets if r.get("name") == name), None)


def get_ruleset(ruleset: str | int) -> dict[str, Any] | None:
    """Fetch the full details of a repository ruleset by name or ID.

    Args:
        ruleset: The ruleset name (``str``) or numeric ruleset ID (``int``).

    Returns:
        The full ruleset dict, or ``None`` if the ruleset could not be found
        or the API call failed (a diagnostic is printed).
    """
    ruleset_id = ruleset
    if isinstance(ruleset, str):
        entry = find_ruleset(ruleset)
        if entry is None:
            return None
        ruleset_id = entry["id"]

    try:
        stdout = subprocess.check_output(
            ["gh", "api", f"repos/:owner/:repo/rulesets/{ruleset_id}"],
            text=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        print(f"  Failed to fetch ruleset {ruleset_id}: {exc.stderr.strip()}")
        return None

    return json.loads(stdout)  # type: ignore[no-any-return]


def update_ruleset(ruleset_id: int, config: dict[str, Any]) -> bool:
    """Update a repository ruleset via the GitHub API.

    Only ``name``, ``target``, ``enforcement``, ``conditions``, ``rules``,
    and ``bypass_actors`` are sent (explicit allowlist to avoid sending
    read-only fields back to the API).

    Args:
        ruleset_id: The numeric ruleset ID to update.
        config: The full ruleset dict (as returned by :func:`get_ruleset`)
            with the desired changes already applied in-memory.

    Returns:
        ``True`` on success, ``False`` if the API call failed (a diagnostic
        is printed).
    """
    payload: dict[str, Any] = {
        "name": config["name"],
        "target": config["target"],
        "enforcement": config["enforcement"],
        "conditions": config["conditions"],
        "rules": config["rules"],
    }
    if "bypass_actors" in config:
        payload["bypass_actors"] = config["bypass_actors"]

    try:
        subprocess.check_output(
            [
                "gh",
                "api",
                "-X",
                "PUT",
                f"repos/:owner/:repo/rulesets/{ruleset_id}",
                "--input",
                "-",
            ],
            input=json.dumps(payload),
            text=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        print(f"  Failed to update ruleset {ruleset_id}: {exc.stderr.strip()}")
        return False

    return True


def get_ruleset_settings_url() -> str | None:
    """Return the URL to the repository's ruleset settings page.

    Returns:
        The URL as a string, or ``None`` if it could not be determined.
    """
    try:
        stdout = subprocess.check_output(
            ["gh", "repo", "view", "--json", "owner,name"],
            text=True,
            stderr=subprocess.PIPE,
        )
        info: dict[str, Any] = json.loads(stdout)
        org = info["owner"]["login"]
        repo = info["name"]
        return f"https://github.com/{org}/{repo}/settings/rules"
    except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError):
        return None


def read_project_type() -> str | None:
    """Read the cookiecutter project type from the replay file."""
    replay_path = Path(".cookiecutter-replay.json")
    if not replay_path.exists():
        return None

    try:
        data = json.loads(replay_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    cookiecutter_data = data.get("cookiecutter")
    if not isinstance(cookiecutter_data, dict):
        return None

    project_type = cookiecutter_data.get("type")
    if not isinstance(project_type, str):
        return None

    return project_type


def read_cookiecutter_github_org() -> str | None:
    """Read the cookiecutter GitHub organization from the replay file."""
    replay_path = Path(".cookiecutter-replay.json")
    if not replay_path.exists():
        return None

    try:
        data = json.loads(replay_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    cookiecutter_data = data.get("cookiecutter")
    if not isinstance(cookiecutter_data, dict):
        return None

    github_org = cookiecutter_data.get("github_org")
    if not isinstance(github_org, str):
        return None

    return github_org


def read_cookiecutter_license() -> str | None:
    """Read the cookiecutter license from the replay file."""
    replay_path = Path(".cookiecutter-replay.json")
    if not replay_path.exists():
        return None

    try:
        data = json.loads(replay_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    cookiecutter_data = data.get("cookiecutter")
    if not isinstance(cookiecutter_data, dict):
        return None

    license_value = cookiecutter_data.get("license")
    if not isinstance(license_value, str):
        return None

    return license_value


def parse_setuptools_version(content: str) -> int | None:
    """Parse the setuptools major version from pyproject content."""
    match = re.search(r'"setuptools\s*==\s*([0-9]+)(?:\.[0-9]+)*"', content)
    if not match:
        return None
    return int(match.group(1))


def replace_setuptools_pin(content: str, new_version: str) -> tuple[str, bool]:
    """Replace the setuptools pin with a new version."""
    new_content, count = re.subn(
        r'("setuptools\s*==\s*)[0-9]+(?:\.[0-9]+)*("\s*,?)',
        rf"\1{new_version}\2",
        content,
        count=1,
    )
    return new_content, count > 0


def migrate_platform_matrix() -> None:
    """Migrate CI matrix from arch+os to a single platform entry.

    This replaces the old matrix definition that used separate `arch` and `os`
    entries with a single `platform` entry using GitHub's native arm64 runners
    that are now available to both public and private repositories.
    """
    workflow_file = Path(".github/workflows/ci.yaml")
    print(f"  - {workflow_file}")
    if not workflow_file.is_file():
        manual_step(
            f"Could not find {workflow_file}; please manually migrate to use a"
            "please manually migrate to use a `platform` matrix entry."
        )
        return

    content = workflow_file.read_text(encoding="utf-8")
    new_content = content

    # Replace the arch+os matrix block with platform.
    # Handle both "arm" (old) and "arm64" (intermediate) variants.
    new_content = re.sub(
        r"( +)arch:\n\1  - amd64\n\1  - arm(?:64)?\n\1os:\n\1  - ubuntu-24\.04\n",
        r"\g<1>platform:\n\g<1>  - ubuntu-24.04\n\g<1>  - ubuntu-24.04-arm\n",
        new_content,
    )

    # Replace any runs-on expression referencing matrix.arch with the simpler
    # matrix.platform reference.
    new_content = re.sub(
        r"runs-on: \$\{\{.*matrix\.arch.*\}\}",
        "runs-on: ${{ matrix.platform }}",
        new_content,
    )

    if new_content == content:
        if "matrix.platform" in content:
            print("    Already uses platform matrix")
        else:
            manual_step(
                f"Could not find arch+os matrix pattern in {workflow_file}; "
                "please manually migrate to use a `platform` matrix entry."
            )
        return

    replace_file_contents_atomically(workflow_file, content, new_content, count=1)
    print("    Migrated arch+os matrix to platform")


def apply_patch(patch_content: str) -> None:
    """Apply a patch using the patch utility."""
    subprocess.run(["patch", "-p1"], input=patch_content.encode(), check=True)


def replace_file_atomically(  # noqa; DOC501, DOC503
    filepath: str | Path, new_content: str
) -> None:
    """Replace a file atomically with the given content.

    The replacement is done atomically by writing to a temporary file in the
    same directory and then moving it to the target location.

    Args:
        filepath: The path to the file to replace.
        new_content: The content to write to the file.
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    tmp_dir = filepath.parent
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # pylint: disable-next=consider-using-with
    tmp = tempfile.NamedTemporaryFile(mode="w", dir=tmp_dir, delete=False)

    try:
        st = None
        try:
            st = os.stat(filepath)
        except FileNotFoundError:
            st = None

        tmp.write(new_content)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()

        if st is not None:
            os.chmod(tmp.name, st.st_mode)

        os.replace(tmp.name, filepath)

    except BaseException:
        tmp.close()
        os.unlink(tmp.name)
        raise


def replace_file_contents_atomically(  # noqa; DOC501
    filepath: str | Path,
    old: str,
    new: str,
    count: SupportsIndex = -1,
    *,
    content: str | None = None,
) -> None:
    """Replace a file atomically with new content.

    The replacement is done atomically by writing to a temporary file and
    then moving it to the target location.

    Args:
        filepath: The path to the file to replace.
        old: The string to replace.
        new: The string to replace it with.
        count: The maximum number of occurrences to replace. If negative, all occurrences are
            replaced.
        content: The content to replace. If not provided, the file is read from disk.
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    if content is None:
        content = filepath.read_text(encoding="utf-8")

    replace_file_atomically(filepath, content.replace(old, new, count))


def calculate_file_sha256_skip_lines(filepath: Path, skip_lines: int) -> str | None:
    """Calculate SHA256 of file contents excluding the first N lines.

    Args:
        filepath: Path to the file to hash
        skip_lines: Number of lines to skip at the beginning

    Returns:
        The SHA256 hex digest, or None if the file doesn't exist
    """
    if not filepath.exists():
        return None

    # Read file and normalize line endings to LF
    content = filepath.read_text(encoding="utf-8").replace("\r\n", "\n")
    # Skip first N lines and ensure there's a trailing newline
    remaining_content = "\n".join(content.splitlines()[skip_lines:]) + "\n"
    return hashlib.sha256(remaining_content.encode()).hexdigest()


def manual_step(message: str) -> None:
    """Print a manual step message in yellow."""
    _manual_steps.append(message)
    print(f"\033[0;33m>>> {message}\033[0m")


if __name__ == "__main__":
    main()
