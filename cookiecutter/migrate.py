#!/usr/bin/env python3
# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Script to migrate existing projects to new versions of the cookiecutter template.

This script migrates existing projects to new versions of the cookiecutter
template, removing the need to completely regenerate the project from
scratch.

To run it, the simplest way is to fetch it from GitHub and run it directly:

    curl -sSLf https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3

Make sure to replace the `<tag>` to the version you want to migrate to in the URL.

For jumping multiple versions you should run the script multiple times, once
for each version.

And remember to follow any manual instructions for each run.
"""  # noqa: E501

# R0801 is similarity detection, as the template is always similar to the current script
# pylint: disable=too-many-lines, too-many-locals, too-many-branches, too-many-statements, R0801

import functools
import hashlib
import json
import os
import re
import shutil
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
    print("Removing unused cross-arch testing files...")
    remove_cross_arch_files()
    print("=" * 72)
    print("Updating cookiecutter replay file...")
    migrate_cookiecutter_replay_file()
    print("=" * 72)
    print("Updating generated CI workflows...")
    migrate_ci_workflows()
    print("=" * 72)
    print("Updating auxiliary GitHub workflows...")
    migrate_auxiliary_workflows()
    print("=" * 72)
    print("Normalizing GitHub Action hashes...")
    migrate_gh_actions_hashes()
    print("=" * 72)
    print("Updating issue template configuration...")
    migrate_issue_templates()
    print("=" * 72)
    print("Setting up the gRPC migration workflow...")
    migrate_grpc_workflow_setup()
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


def remove_cross_arch_files() -> None:
    """Remove unused cross-arch testing containers and documentation.

    The cross-arch QEMU-based testing infrastructure has been removed from
    the template.  The corresponding GitHub Actions have been archived:

    - frequenz-floss/gh-action-nox-cross-arch
    - frequenz-floss/gh-action-test-pip-install-cross-arch
    - frequenz-floss/gh-action-run-python-in-qemu

    This step removes the leftover container files and the "Cross-Arch
    Testing" section from CONTRIBUTING.md.  Before removing anything it
    checks that no workflow still references the files or actions.
    """
    # Heuristic: if any workflow still references cross-arch containers or
    # the archived actions, bail out and ask for manual intervention.
    cross_arch_patterns = [
        "nox-cross-arch",
        "test-pip-install-cross-arch",
        "run-python-in-qemu",
    ]
    workflows_dir = Path(".github/workflows")
    if workflows_dir.is_dir():
        for wf in sorted(workflows_dir.iterdir()):
            if wf.suffix not in (".yml", ".yaml"):
                continue
            try:
                content = wf.read_text(encoding="utf-8")
            except OSError:
                continue
            for pattern in cross_arch_patterns:
                if pattern in content:
                    manual_step(
                        f"{wf} still references '{pattern}'. "
                        "Please remove those references before deleting the "
                        "cross-arch container files."
                    )
                    return

    # Files and directories to remove.
    paths_to_remove = [
        Path(".github/containers/nox-cross-arch"),
        Path(".github/containers/test-installation"),
    ]

    for path in paths_to_remove:
        if not path.exists():
            print(f"  Skipped {path}: does not exist")
            continue
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"  Removed {path}")
        except OSError as exc:
            manual_step(f"Failed to remove {path}: {exc}")

    # Clean up the now-empty .github/containers directory if present.
    containers_dir = Path(".github/containers")
    if containers_dir.is_dir():
        try:
            remaining: list[Path | None] = list(containers_dir.iterdir())
        except OSError:
            remaining = [None]  # non-empty sentinel
        if not remaining:
            try:
                containers_dir.rmdir()
                print(f"  Removed empty {containers_dir}")
            except OSError as exc:
                manual_step(f"Failed to remove empty {containers_dir}: {exc}")

    # Remove the "Cross-Arch Testing" section from CONTRIBUTING.md.
    contributing = Path("CONTRIBUTING.md")
    if not contributing.exists():
        print(f"  Skipped {contributing}: does not exist")
        return

    try:
        text = contributing.read_text(encoding="utf-8")
    except OSError as exc:
        manual_step(f"Failed to read {contributing}: {exc}")
        return

    section_header = "##  Cross-Arch Testing"
    if section_header not in text:
        print(f"  Skipped {contributing}: 'Cross-Arch Testing' section not found")
        return

    # Drop everything from the section header to the end of the file (the
    # section was always the last one) or up to the next same-level heading.
    lines = text.split("\n")
    new_lines: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith(section_header):
            in_section = True
            # Remove the blank line just before the heading if present.
            while new_lines and new_lines[-1].strip() == "":
                new_lines.pop()
            continue
        if in_section and line.startswith("## "):
            in_section = False
        if not in_section:
            new_lines.append(line)

    new_text = "\n".join(new_lines)
    if not new_text.endswith("\n"):
        new_text += "\n"

    try:
        replace_file_atomically(contributing, new_text)
        print(f"  Updated {contributing}: removed 'Cross-Arch Testing' section")
    except OSError as exc:
        manual_step(
            f"Failed to update {contributing}: {exc}. "
            "Please remove the 'Cross-Arch Testing' section manually."
        )


def migrate_cookiecutter_replay_file() -> None:
    """Add new template inputs to the stored cookiecutter replay file."""
    replay_path = Path(".cookiecutter-replay.json")
    if not replay_path.exists():
        print(f"  Skipped {replay_path}: file not found")
        return

    try:
        data = json.loads(replay_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        manual_step(
            f"Could not update {replay_path}. Please add the new `private_repo` "
            f"variable manually ({error})."
        )
        return

    cookiecutter_data = data.get("cookiecutter")
    if not isinstance(cookiecutter_data, dict):
        manual_step(
            f"Could not update {replay_path}: missing `cookiecutter` object. "
            "Please add `private_repo` manually."
        )
        return

    private_repo_value = "yes" if _infer_private_repo() else "no"
    updated_cookiecutter = _insert_key_after(
        cookiecutter_data,
        after_key="license",
        key="private_repo",
        value=private_repo_value,
    )
    data["cookiecutter"] = updated_cookiecutter

    replay_template_data = data.get("_cookiecutter")
    if isinstance(replay_template_data, dict):
        data["_cookiecutter"] = _insert_key_after(
            replay_template_data,
            after_key="license",
            key="private_repo",
            value=_PRIVATE_REPO_COOKIECUTTER_OPTIONS,
        )

    new_content = json.dumps(data, indent=2)
    if not new_content.endswith("\n"):
        new_content += "\n"

    normalized_old = _normalize_content(replay_path.read_text(encoding="utf-8"))
    if new_content == normalized_old:
        print(f"  Skipped {replay_path}: already has the expected updates")
        return

    replace_file_atomically(replay_path, new_content)
    print(
        f"  Updated {replay_path}: added `private_repo={private_repo_value}` replay data"
    )


def migrate_ci_workflows() -> None:
    """Update the generated CI workflows to the latest template."""
    private_repo = _infer_private_repo()

    _update_workflow_private_repo_settings(
        Path(".github/workflows/ci-pr.yaml"),
        private_repo=private_repo,
        description="adjusted CI pull-request privacy settings",
    )
    _update_workflow_private_repo_settings(
        Path(".github/workflows/ci.yaml"),
        private_repo=private_repo,
        description="adjusted main CI privacy settings",
    )


def migrate_auxiliary_workflows() -> None:
    """Update the remaining generated GitHub workflows."""
    private_repo = _infer_private_repo()
    _update_workflow_private_repo_settings(
        Path(".github/workflows/release-notes-check.yml"),
        private_repo=private_repo,
        description="adjusted release notes privacy settings",
    )
    _migrate_dependabot_migration_workflows()


def _migrate_dependabot_migration_workflows() -> None:
    """Use the unreleased Dependabot migration action features explicitly."""
    _migrate_black_migration_workflow()
    _migrate_repo_config_migration_workflow()


def _migrate_black_migration_workflow() -> None:
    """Update the black migration workflow to use explicit version iteration."""
    path = Path(".github/workflows/black-migration.yaml")
    content = _read_expected_workflow(path)
    if content is None:
        return

    original = content
    content = _update_dependabot_migrate_action_ref(content)
    content = _ensure_line_after(
        content,
        path=path,
        anchor='          auto-merge-on-changes: "false"\n',
        line='          version-iteration: "false"\n',
    )

    if content == original:
        print(f"  Skipped {path}: already up to date")
        return

    replace_file_atomically(path, content)
    print(f"  Updated {path}: use explicit Dependabot migration iteration")


def _migrate_repo_config_migration_workflow() -> None:
    """Update the repo-config migration workflow to use minor iteration."""
    path = Path(".github/workflows/repo-config-migration.yaml")
    content = _read_expected_workflow(path)
    if content is None:
        return

    original = content
    content = _update_dependabot_migrate_action_ref(content)
    content = _ensure_line_after(
        content,
        path=path,
        anchor="          migration-token: ${{ secrets.REPO_CONFIG_MIGRATION_TOKEN }}\n",
        line='          version-iteration: "minor"\n',
    )
    content = _ensure_line_after(
        content,
        path=path,
        anchor='          version-iteration: "minor"\n',
        line='          if-no-iterations: "pass"\n',
    )

    if content == original:
        print(f"  Skipped {path}: already up to date")
        return

    replace_file_atomically(path, content)
    print(f"  Updated {path}: use explicit Dependabot migration iteration")


def _read_expected_workflow(path: Path) -> str | None:
    """Read an expected workflow file and normalize its line endings."""
    if not path.exists():
        manual_step(
            f"{path} is missing. Generated projects are expected to have this "
            "workflow; please restore it from the template or apply the "
            "Dependabot migration workflow updates manually."
        )
        return None

    return _normalize_content(path.read_text(encoding="utf-8"))


def _update_dependabot_migrate_action_ref(content: str) -> str:
    """Point the Dependabot migration action to the testing branch."""
    return re.sub(
        r"^        uses: frequenz-floss/gh-action-dependabot-migrate@[^\n]*$",
        r"        uses: frequenz-floss/gh-action-dependabot-migrate@"
        r"27763fb5eb56476d91abe00132e8a0614171f92f # v1.2.0",
        content,
        count=1,
        flags=re.MULTILINE,
    )


def _ensure_line_after(content: str, *, path: Path, anchor: str, line: str) -> str:
    """Ensure ``line`` exists immediately after a known workflow input line."""
    if line in content:
        return content
    if anchor not in content:
        manual_step(
            f"{path} does not match the expected layout; please add "
            f"{line.strip()!r} manually."
        )
        return content
    return content.replace(anchor, anchor + line, 1)


def migrate_gh_actions_hashes() -> None:
    """Update GitHub Action hashes to point to the actual commit object.

    The hashes we were using are the annotated git tag object, but
    Dependabot likes to have the pins to the actual commit object the
    tag points to, not the tag itself.
    """
    replacements = [
        (
            "frequenz-floss/gh-action-setup-git@16952aac3ccc01d27412fe0dea3ea946530dcace",
            "frequenz-floss/gh-action-setup-git@f9d86a01228ee1cadaac5224d4d7626f1eb23f90",
        ),
        (
            "frequenz-floss/gh-action-setup-python-with-deps@"
            "0d0d77eac3b54799f31f25a1060ef2c6ebdf9299",  # noqa: E501
            "frequenz-floss/gh-action-setup-python-with-deps@e4d0b2ef8f5a1612d7827f3abaef17c931d2b946",  # noqa: E501
        ),
    ]

    workflows_dir = Path(".github/workflows")
    if not workflows_dir.is_dir():
        print(f"  Skipped {workflows_dir}: directory not found")
        return

    for wf in sorted(workflows_dir.iterdir()):
        if wf.suffix not in (".yml", ".yaml"):
            continue
        try:
            content = wf.read_text(encoding="utf-8")
        except OSError:
            continue

        new_content = content
        for old, new in replacements:
            new_content = new_content.replace(old, new)

        if new_content != content:
            replace_file_atomically(wf, new_content)
            print(f"  Updated {wf}: normalized GitHub Action hashes")


_GRPC_MIGRATION_WORKFLOW_CONTENT = (
    """\
# Automatic grpc/protobuf build/runtime sync for Dependabot PRs
#
# The template's `pyproject.toml` pins `protobuf`, `grpcio` and `grpcio-tools`
# in `[build-system].requires` as *exact* versions, and also declares
# `protobuf` and `grpcio` in `[project].dependencies` with a `>= <build-pin>`
# lower bound.  The lower bound must always match the exact pin, because the
# protobuf cross-version runtime guarantee requires the runtime to be at
# least the version used at generation time:
#   https://protobuf.dev/support/cross-version-runtime-guarantee/
#
# Dependabot correctly bumps `[build-system].requires`, but it does not bump
# the matching `>=` floor in `[project].dependencies`.  This workflow runs
# after a Dependabot grpc/protobuf group PR, rewrites the `>=` floor to match
# the new build pins, and pushes the fix-up commit back onto the PR branch.
#
# The companion auto-dependabot workflow skips the `grpc-compatible`,
# `grpcio-major` and `protobuf-major` groups so those PRs are handled
# exclusively by this migration workflow.
#
# XXX: !!! SECURITY WARNING !!!
# pull_request_target has write access to the repo, and can read secrets.
# This is required because Dependabot PRs are treated as fork PRs: the
# GITHUB_TOKEN is read-only and secrets are unavailable with a plain
# pull_request trigger.  The action mitigates the risk by:
#   - Never executing code from the PR (the migration script is fetched
#     from the repo-config branch configured below, not taken from the PR).
#   - Gating migration steps on github.actor == 'dependabot[bot]' AND the
#     PR title.
#   - Running checkout with persist-credentials: false and isolating
#     push credentials from the migration script environment.
# For more details read:
# https://securitylab.github.com/research/github-actions-preventing-pwn-requests/

name: gRPC Migration

on:
  merge_group:  # To allow using this as a required check for merging
  pull_request_target:
    types: [opened, synchronize, reopened, labeled, unlabeled]

permissions:
  # Commit the sync-up to the PR branch.
  contents: write
  # Create and normalize migration state labels.
  issues: write
  # Read/update pull request metadata and comments.
  pull-requests: write

jobs:
  grpc-migration:
    name: Fix gRPC/protobuf runtime floors
    # Skip if it was triggered by the merge queue. We only need the workflow to
    # be executed to meet the "Required check" condition for merging, but we
    # don't need to actually run the job, having the job present as Skipped is
    # enough.
    if: |
      github.event_name == 'pull_request_target' &&
      github.actor == 'dependabot[bot]' &&
      (contains(github.event.pull_request.title, 'the grpc-compatible group') ||
       contains(github.event.pull_request.title, 'the grpcio-major group') ||
       contains(github.event.pull_request.title, 'the protobuf-major group'))
    runs-on: ubuntu-24.04
    steps:
      - name: Generate token
        id: create-app-token
        uses: actions/create-github-app-token@1b10c78c7865c340bc4f6099eb2f838309f1e8c3 # v3.1.1
        with:
          app-id: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_ID }}
          private-key: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY }}
          # Push the sync-up commit to the PR branch.
          permission-contents: write
          # Create and normalize migration state labels.
          permission-issues: write
          # Read/update pull request metadata and labels.
          permission-pull-requests: write
      - name: Migrate
        uses: frequenz-floss/gh-action-dependabot-migrate@"""  # Avoid going over 100 chars
    + """27763fb5eb56476d91abe00132e8a0614171f92f # v1.2.0
        with:
          script-url-template: >- # v0.18.0
            https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/"""
    + """529d30b554392e6d8b66e84e92c04ac9cd170da7/cookiecutter/scripts/dependabot-grpc-fixer.py
          token: ${{ steps.create-app-token.outputs.token }}
          version-iteration: "false"
          sign-commits: "true"
          auto-merged-label: "tool:auto-merged"
          migrated-label: "tool:grpc:migration:executed"
          intervention-pending-label: "tool:grpc:migration:intervention-pending"
          intervention-done-label: "tool:grpc:migration:intervention-done"
"""
)
"""Final content of the grpc-migration workflow installed by the migration."""

_OLD_GRPC_GROUP_BLOCK = """\
      grpc:
        patterns:
          - "grpcio"
          - "grpcio-tools"
          - "protobuf"
"""
"""Verbatim representation of the old monolithic 'grpc' Dependabot group."""

_NEW_GRPC_GROUPS_BLOCK = """\
      # We group grpcio and protobuf updates together, as they need special
      # handling on the pyproject.toml file because of the protobuf/grpcio
      # build/runtime cross-version guarantees and wrong dependabot handling
      # of build/runtime dependencies.
      grpc-compatible:
        update-types:
          - "patch"
          - "minor"
        patterns:
          - "grpcio"
          - "grpcio-tools"
          - "protobuf"
      # For major updates we split it up. It was observed in the past that
      # grpcio releases lag behind protobuf releases, and they are not
      # compatible with a major protobuf update for a while, so we shouldn't
      # block the update of one with the other.
      grpcio-major:
        patterns:
          - "grpcio"
          - "grpcio-tools"
      protobuf-major:
        patterns:
          - "protobuf"
"""
"""The three new Dependabot groups that replace the old 'grpc' group."""

_GRPC_EXCLUDE_PATTERN_NAMES = ("grpcio", "grpcio-tools", "protobuf")
"""Package names that must be excluded from broad Dependabot groups."""


def migrate_issue_templates() -> None:
    """Update issue template configuration for repository privacy.

    Public repositories include a ``contact_links`` entry that points
    users to GitHub Discussions.  Private repositories should not have
    this section because Discussions are typically disabled.

    If the file does not exist it is created from scratch, matching what
    the cookiecutter template would produce for the inferred privacy
    setting.
    """
    config_path = Path(".github/ISSUE_TEMPLATE/config.yml")
    private_repo = _infer_private_repo()

    if not config_path.exists():
        content = _create_issue_template_config(private_repo=private_repo)
        if content is None:
            return
        config_path.parent.mkdir(parents=True, exist_ok=True)
        replace_file_atomically(config_path, content)
        print(f"  Created {config_path}")
        return

    content = _normalize_content(config_path.read_text(encoding="utf-8"))

    if private_repo:
        updated = _remove_issue_template_contact_links(content)
    else:
        updated = _ensure_issue_template_contact_links(content)

    if updated == content:
        print(f"  Skipped {config_path}: already up to date")
        return

    replace_file_atomically(config_path, updated)
    print(f"  Updated {config_path}: adjusted contact_links for privacy settings")


_ISSUE_TEMPLATE_CONFIG_HEADER = (
    "# GitHub issue template chooser. For more information see:\n"
    "# https://docs.github.com/en/communities/using-templates-to-encourage"
    "-useful-issues-and-pull-requests/configuring-issue-templates-for-your"
    "-repository#configuring-the-template-chooser\n"
    "\n"
    "blank_issues_enabled: true\n"
)

_ISSUE_TEMPLATE_CONTACT_LINKS_BLOCK = (
    "contact_links:\n"
    "  - name: Ask a question ❓\n"
    "    url: https://github.com/{github_org}/{github_repo_name}"
    "/discussions/new?category=support\n"
    "    # TODO(cookiecutter): Make sure the GitHub repository has a "
    'discussion category "Support"\n'
    '    # Rename the "Q&A" category to "Support" and change the emoji '
    "to 🆘 (SOS)\n"
    "    about: Use this if you are not sure how to do something, "
    "have installation problems, etc.\n"
)


def _create_issue_template_config(*, private_repo: bool) -> str | None:
    """Create the issue template config content from scratch.

    Args:
        private_repo: Whether the repository is private.

    Returns:
        The file content, or ``None`` if the necessary metadata could not
        be read and a manual step was emitted instead.
    """
    if private_repo:
        return _ISSUE_TEMPLATE_CONFIG_HEADER

    github_org = read_cookiecutter_str_var("github_org")
    github_repo_name = read_cookiecutter_str_var("github_repo_name")
    if not github_org or not github_repo_name:
        manual_step(
            "Cannot create .github/ISSUE_TEMPLATE/config.yml: "
            "github_org or github_repo_name not found in "
            ".cookiecutter-replay.json. Please create the file manually "
            "(see the cookiecutter template for reference)."
        )
        return None

    manual_step(
        "Make sure the GitHub repository has a discussion category "
        '"Support". Rename the "Q&A" category to "Support" and change '
        "the emoji to 🆘 (SOS)."
    )
    return _ISSUE_TEMPLATE_CONFIG_HEADER + _ISSUE_TEMPLATE_CONTACT_LINKS_BLOCK.format(
        github_org=github_org,
        github_repo_name=github_repo_name,
    )


def _remove_issue_template_contact_links(content: str) -> str:
    """Remove the ``contact_links`` section from issue template config."""
    return (
        re.sub(
            r"^contact_links:\n(?:[ \t]+[^\n]*\n)*",
            "",
            content,
            flags=re.MULTILINE,
        ).rstrip("\n")
        + "\n"
    )


def _ensure_issue_template_contact_links(content: str) -> str:
    """Ensure the ``contact_links`` section is present in the config."""
    if "contact_links:" in content:
        return content

    github_org = read_cookiecutter_str_var("github_org")
    github_repo_name = read_cookiecutter_str_var("github_repo_name")
    if not github_org or not github_repo_name:
        manual_step(
            "Cannot restore contact_links in .github/ISSUE_TEMPLATE/config.yml: "
            "github_org or github_repo_name not found in .cookiecutter-replay.json. "
            "Please add the contact_links section manually."
        )
        return content

    block = _ISSUE_TEMPLATE_CONTACT_LINKS_BLOCK.format(
        github_org=github_org,
        github_repo_name=github_repo_name,
    )
    return content.rstrip("\n") + "\n" + block


_SETUP_GIT_DISABLED_BLOCK = (
    "        # TODO(cookiecutter): Uncomment this for projects with private "
    "dependencies\n"
    "        # with:\n"
    "        #   username: ${{ secrets.GIT_USER }}\n"
    "        #   password: ${{ secrets.GIT_PASS }}\n"
)

_SETUP_GIT_ENABLED_BLOCK = (
    "        with:\n"
    "          username: ${{ secrets.GIT_USER }}\n"
    "          password: ${{ secrets.GIT_PASS }}\n"
)

_NOX_PRIVATE_DEPS_DISABLED_BLOCK = (
    "          # TODO(cookiecutter): Uncomment this for projects with private "
    "dependencies\n"
    "          # git-username: ${{ secrets.GIT_USER }}\n"
    "          # git-password: ${{ secrets.GIT_PASS }}\n"
)

_NOX_PRIVATE_DEPS_ENABLED_BLOCK = (
    "          git-username: ${{ secrets.GIT_USER }}\n"
    "          git-password: ${{ secrets.GIT_PASS }}\n"
)

_RELEASE_NOTES_TOKEN_DISABLED_BLOCK = (
    "          # TODO(cookiecutter): Uncomment the following line for private "
    "repositories, otherwise remove it\n"
    "          # token: ${{ secrets.github_token }}\n"
)

_RELEASE_NOTES_TOKEN_ENABLED_BLOCK = "          token: ${{ secrets.github_token }}\n"

_CREATE_GITHUB_RELEASE_PUBLIC_NEEDS = (
    "  create-github-release:\n"
    "    name: Create GitHub release\n"
    '    needs: ["publish-docs"]\n'
)
_CREATE_GITHUB_RELEASE_PRIVATE_NEEDS = (
    "  create-github-release:\n"
    "    name: Create GitHub release\n"
    '    needs: ["nox-all", "test-installation-all"]\n'
)

_PRIVATE_REPO_COOKIECUTTER_OPTIONS = [
    "{{ 'yes' if cookiecutter.license == 'Proprietary' else 'no' }}",
    "{{ 'no' if cookiecutter.license == 'Proprietary' else 'yes' }}",
]


def _normalize_content(content: str) -> str:
    """Normalize content for stable hashing and comparisons."""
    content = content.replace("\r\n", "\n")
    if not content.endswith("\n"):
        content += "\n"
    return content


def _set_optional_block(
    content: str, *, disabled: str, enabled: str, include_enabled: bool
) -> str:
    """Set a generated optional workflow block to the desired state."""
    if include_enabled:
        return content.replace(disabled, enabled)
    return content.replace(disabled, "").replace(enabled, "")


def _remove_job(content: str, job_name: str) -> str:
    """Remove a top-level workflow job by name."""
    pattern = re.compile(
        rf"^  {re.escape(job_name)}:\n.*?(?=^  [a-z0-9-]+:|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    return pattern.sub("", content)


def _adjust_ci_workflow_private_repo_settings(
    content: str, *, private_repo: bool
) -> str:
    """Adjust CI workflow sections that depend on repository privacy."""
    content = _set_optional_block(
        content,
        disabled=_SETUP_GIT_DISABLED_BLOCK,
        enabled=_SETUP_GIT_ENABLED_BLOCK,
        include_enabled=private_repo,
    )
    content = _set_optional_block(
        content,
        disabled=_NOX_PRIVATE_DEPS_DISABLED_BLOCK,
        enabled=_NOX_PRIVATE_DEPS_ENABLED_BLOCK,
        include_enabled=private_repo,
    )
    content = content.replace(
        _CREATE_GITHUB_RELEASE_PUBLIC_NEEDS,
        (
            _CREATE_GITHUB_RELEASE_PRIVATE_NEEDS
            if private_repo
            else _CREATE_GITHUB_RELEASE_PUBLIC_NEEDS
        ),
    )
    content = content.replace(
        _CREATE_GITHUB_RELEASE_PRIVATE_NEEDS,
        (
            _CREATE_GITHUB_RELEASE_PRIVATE_NEEDS
            if private_repo
            else _CREATE_GITHUB_RELEASE_PUBLIC_NEEDS
        ),
    )

    if private_repo:
        content = _remove_job(content, "publish-docs")
        content = _remove_job(content, "publish-to-pypi")

    content = re.sub(r"[ \t]+\n", "\n", content)
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content


def _adjust_release_notes_check_private_repo_settings(
    content: str, *, private_repo: bool
) -> str:
    """Adjust release-notes workflow sections that depend on privacy."""
    return _set_optional_block(
        content,
        disabled=_RELEASE_NOTES_TOKEN_DISABLED_BLOCK,
        enabled=_RELEASE_NOTES_TOKEN_ENABLED_BLOCK,
        include_enabled=private_repo,
    )


def _update_workflow_private_repo_settings(
    filepath: Path, *, private_repo: bool, description: str
) -> None:
    """Update workflow sections that depend on repository privacy."""
    if not filepath.exists():
        return

    content = _normalize_content(filepath.read_text(encoding="utf-8"))

    match filepath.name:
        case "ci.yaml" | "ci-pr.yaml":
            updated = _adjust_ci_workflow_private_repo_settings(
                content, private_repo=private_repo
            )
        case "release-notes-check.yml":
            updated = _adjust_release_notes_check_private_repo_settings(
                content, private_repo=private_repo
            )
        case _:
            return

    if updated == content:
        return

    replace_file_atomically(filepath, updated)
    print(f"  Updated {filepath}: {description}")


def _insert_key_after(
    data: dict[str, Any], *, after_key: str, key: str, value: Any
) -> dict[str, Any]:
    """Insert or update a key immediately after another key in a dict."""
    if key in data:
        data[key] = value
        return data

    updated: dict[str, Any] = {}
    inserted = False
    for existing_key, existing_value in data.items():
        updated[existing_key] = existing_value
        if existing_key == after_key:
            updated[key] = value
            inserted = True

    if not inserted:
        updated[key] = value

    return updated


@functools.lru_cache(maxsize=1)
def _infer_private_repo() -> bool:
    """Infer whether the repository should be treated as private.

    The authoritative source is the actual GitHub repository visibility,
    queried via the ``gh`` CLI.  When that is not available (no ``gh``
    installed, no network, not inside a GitHub-hosted repo, etc.) we fall
    back to heuristics based on the cookiecutter replay file and
    ``pyproject.toml``.  A manual-step warning is only emitted when no
    local metadata is available at all and we have to fall back to a
    hard-coded default.
    """
    github_private = _query_github_visibility()
    if github_private is not None:
        return github_private

    # Fallback: infer from project metadata.
    inferred = _infer_private_repo_from_metadata()
    if inferred is not None:
        label = "private" if inferred else "public"
        manual_step(
            "  Could not determine repository visibility from GitHub (is the `gh` "
            f"CLI installed and authenticated?). Inferred the repo is {label} from "
            "project metadata. If that is wrong, set `private_repo` in "
            ".cookiecutter-replay.json and re-run."
        )
        return inferred

    manual_step(
        "Could not determine repository visibility from GitHub or "
        "project metadata. Assuming the repo is *public*. If that is "
        "wrong, set `private_repo` in .cookiecutter-replay.json and "
        "re-run."
    )
    return False


def _query_github_visibility() -> bool | None:
    """Query the actual GitHub repository visibility via the ``gh`` CLI.

    Returns:
        ``True`` for private repos, ``False`` for public ones, or ``None``
        if the visibility could not be determined.
    """
    try:
        stdout = subprocess.check_output(
            ["gh", "repo", "view", "--json", "isPrivate"],
            text=True,
            stderr=subprocess.PIPE,
        )
        data = json.loads(stdout)
        value = data["isPrivate"]
        if isinstance(value, bool):
            return value
        print(f"  Unexpected 'isPrivate' value from gh: {value!r}")
    except FileNotFoundError:
        print("  gh CLI not found; cannot query repository visibility.")
    except subprocess.CalledProcessError as exc:
        print(f"  Failed to query repository visibility: {exc.stderr.strip()}")
    except (json.JSONDecodeError, KeyError):
        print("  Unexpected response from gh; cannot determine visibility.")

    return None


def _infer_private_repo_from_metadata() -> bool | None:
    """Infer repository privacy from project metadata (best-effort).

    Checks, in order: the ``private_repo`` cookiecutter variable, the
    ``license`` cookiecutter variable, and the ``pyproject.toml`` license
    field.  Returns ``None`` when no source provides a usable signal.
    """
    if private_repo := read_cookiecutter_str_var("private_repo"):
        return private_repo == "yes"

    if license_name := read_cookiecutter_str_var("license"):
        return license_name == "Proprietary"

    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        pyproject_content = pyproject_path.read_text(encoding="utf-8")
        if 'license = "LicenseRef-Proprietary"' in pyproject_content:
            return True
        if 'license = "MIT"' in pyproject_content:
            return False

    return None


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


def read_cookiecutter_str_var(name: str) -> str | None:
    """Read a cookiecutter variable from the replay file."""
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

    value = cookiecutter_data.get(name)
    if not isinstance(value, str):
        return None

    return value


def migrate_grpc_workflow_setup() -> None:
    """Set up the gRPC migration workflow for API repositories.

    Only API repositories pin grpc/protobuf as build-time dependencies and
    therefore need the dedicated migration workflow.  For all other project
    types this step is a no-op.

    For API repositories the step:

    * Updates ``.github/dependabot.yml`` to add the new
      ``grpc-compatible`` / ``grpcio-major`` / ``protobuf-major`` groups
      (replacing any old ``grpc`` group), and to exclude grpc/protobuf
      packages from the ``patch`` and ``minor`` groups.
    * Updates ``.github/workflows/auto-dependabot.yaml`` so the new grpc
      group PRs are skipped by the auto-merge workflow.
    * Installs (or replaces) ``.github/workflows/grpc-migration.yaml``.
    * Adds ``Fix gRPC/protobuf runtime floors`` to the
      ``Protect version branches`` GitHub ruleset.
    """
    project_type = read_cookiecutter_str_var("type")
    if project_type != "api":
        print(
            "  Skipped: not an API project "
            f"(type={project_type!r}); the gRPC migration workflow is only "
            "needed for API repositories."
        )
        return

    _migrate_grpc_dependabot_config()
    _migrate_grpc_auto_dependabot_workflow()
    _install_grpc_migration_workflow()
    _migrate_grpc_ruleset()


def _migrate_grpc_dependabot_config() -> None:
    """Update ``.github/dependabot.yml`` for the new grpc grouping."""
    path = Path(".github/dependabot.yml")
    if not path.exists():
        manual_step(
            f"{path} not found; please update it manually to use the new "
            "grpc-compatible / grpcio-major / protobuf-major Dependabot "
            "groups (see the cookiecutter template for reference)."
        )
        return

    original = _normalize_content(path.read_text(encoding="utf-8"))
    content = original
    notes: list[str] = []

    content, group_note = _update_grpc_groups(content)
    if group_note:
        notes.append(group_note)

    content, exclude_note = _ensure_grpc_exclude_patterns(content)
    if exclude_note:
        notes.append(exclude_note)

    if content == original:
        print(f"  Skipped {path}: already up to date")
        return

    replace_file_atomically(path, content)
    print(f"  Updated {path}: " + "; ".join(notes))


def _update_grpc_groups(content: str) -> tuple[str, str | None]:
    """Replace the old grpc group with the new three groups, or insert them.

    If a customized ``grpc:`` group is detected (i.e. the file has an entry
    matching ``      grpc:`` but the surrounding content does not match the
    old default verbatim) a manual-step warning is emitted and the content
    is returned unchanged.
    """
    if _NEW_GRPC_GROUPS_BLOCK in content:
        return content, None

    if _OLD_GRPC_GROUP_BLOCK in content:
        return (
            content.replace(_OLD_GRPC_GROUP_BLOCK, _NEW_GRPC_GROUPS_BLOCK, 1),
            "replaced old 'grpc' group with grpc-compatible / "
            "grpcio-major / protobuf-major",
        )

    if re.search(r"^      grpc:\s*$", content, flags=re.MULTILINE):
        manual_step(
            ".github/dependabot.yml has a customized 'grpc:' Dependabot "
            "group.  Please replace it manually with the new "
            "'grpc-compatible', 'grpcio-major' and 'protobuf-major' "
            "groups (see the cookiecutter template for reference)."
        )
        return content, None

    # No grpc group present: append the three new groups to the existing
    # `groups:` block of the pip ecosystem.  We anchor on the well-known
    # `mkdocstrings` group, which is the last group emitted by the
    # template, to keep the insertion point deterministic.
    mkdocstrings_pattern = re.compile(
        r"(      mkdocstrings:\n"
        r"        patterns:\n"
        r'          - "mkdocstrings\*"\n'
        r'          - "mkdocstrings\[python\]"\n)',
    )
    match = mkdocstrings_pattern.search(content)
    if match is None:
        manual_step(
            ".github/dependabot.yml does not contain the expected "
            "'mkdocstrings' Dependabot group; cannot insert the new grpc "
            "groups automatically.  Please add the 'grpc-compatible', "
            "'grpcio-major' and 'protobuf-major' groups manually (see the "
            "cookiecutter template for reference)."
        )
        return content, None

    insertion = match.group(1) + _NEW_GRPC_GROUPS_BLOCK
    return (
        content[: match.start()] + insertion + content[match.end() :],
        "added grpc-compatible / grpcio-major / protobuf-major groups",
    )


def _ensure_grpc_exclude_patterns(content: str) -> tuple[str, str | None]:
    """Add the grpc exclude-patterns block to ``patch`` and ``minor`` groups.

    Idempotent: if both groups already declare the grpc/protobuf packages
    as ``exclude-patterns`` this function is a no-op.  When a group is
    missing some packages, only those missing entries are appended at the
    end of the existing ``exclude-patterns`` list.
    """
    updated = content
    changed_groups: list[str] = []

    for group_name in ("patch", "minor"):
        new = _ensure_grpc_exclude_in_group(updated, group_name)
        if new != updated:
            updated = new
            changed_groups.append(group_name)

    if not changed_groups:
        return content, None
    return updated, "added grpc exclude-patterns to " + " and ".join(changed_groups)


def _ensure_grpc_exclude_in_group(content: str, group_name: str) -> str:
    """Add the grpc exclude-patterns block to a single Dependabot group."""
    # Match the group header followed by its body up to (but not including)
    # the next sibling key (8 spaces) or the next top-level dash.
    group_pattern = re.compile(
        rf"(      {re.escape(group_name)}:\n"
        rf"(?:        [^\n]*\n)*?"
        rf"        exclude-patterns:\n"
        rf"((?:          [^\n]*\n)*))",
    )

    match = group_pattern.search(content)
    if match is None:
        return content

    existing_excludes = match.group(2)
    missing = [
        name
        for name in _GRPC_EXCLUDE_PATTERN_NAMES
        if f'"{name}"' not in existing_excludes
    ]
    if not missing:
        return content

    # Append only missing dependencies, so partially migrated/customized
    # projects do not get duplicate exclude-patterns.
    if any(name in existing_excludes for name in _GRPC_EXCLUDE_PATTERN_NAMES):
        missing_block = "".join(f'          - "{name}"\n' for name in missing)
    else:
        missing_block = (
            "          # These need a migration script to fix Dependabot not updating the\n"
            "          # runtime dependencies\n"
            + "".join(f'          - "{name}"\n' for name in missing)
        )

    new_block = match.group(1) + missing_block
    return content[: match.start()] + new_block + content[match.end() :]


_AUTO_DEPENDABOT_GRPC_GROUPS = (
    "the grpc-compatible group",
    "the grpcio-major group",
    "the protobuf-major group",
)
"""Dependabot PR title fragments handled by the grpc migration workflow."""


def _migrate_grpc_auto_dependabot_workflow() -> None:
    """Update auto-dependabot.yaml to skip the new grpc group PRs."""
    path = Path(".github/workflows/auto-dependabot.yaml")
    if not path.exists():
        # Some older repos used `.yml`.
        alt = Path(".github/workflows/auto-dependabot.yml")
        if alt.exists():
            path = alt
        else:
            manual_step(
                "Cannot find .github/workflows/auto-dependabot.yaml; "
                "please add the new grpc-compatible / grpcio-major / "
                "protobuf-major skip conditions manually (see the "
                "cookiecutter template for reference)."
            )
            return

    content = _normalize_content(path.read_text(encoding="utf-8"))
    missing_groups = [
        group for group in _AUTO_DEPENDABOT_GRPC_GROUPS if group not in content
    ]
    if not missing_groups:
        print(f"  Skipped {path}: already skips grpc Dependabot groups")
        return

    anchor = (
        "      !contains(github.event.pull_request.title, "
        "'the repo-config group') &&\n"
    )
    if anchor not in content:
        manual_step(
            f"{path} does not match the expected layout; please add "
            "skip conditions for "
            + ", ".join(f"'{group}'" for group in missing_groups)
            + " manually."
        )
        return

    missing_lines = "".join(
        "      !contains(github.event.pull_request.title, " f"'{group}') &&\n"
        for group in missing_groups
    )
    updated = content.replace(anchor, anchor + missing_lines, 1)
    replace_file_atomically(path, updated)
    print(f"  Updated {path}: skip the new grpc Dependabot groups")


def _install_grpc_migration_workflow() -> None:
    """Install or replace the grpc-migration workflow file.

    The workflow is always overwritten because some repositories carry
    earlier experimental versions of it that need to be brought up to the
    final shape.
    """
    path = Path(".github/workflows/grpc-migration.yaml")
    path.parent.mkdir(parents=True, exist_ok=True)

    new_content = _GRPC_MIGRATION_WORKFLOW_CONTENT
    if path.exists():
        old_content = _normalize_content(path.read_text(encoding="utf-8"))
        if old_content == new_content:
            print(f"  Skipped {path}: already up to date")
            return
        replace_file_atomically(path, new_content)
        print(f"  Updated {path}: replaced with the latest workflow")
        return

    replace_file_atomically(path, new_content)
    print(f"  Created {path}")


_GRPC_REQUIRED_CHECK_CONTEXT = "Fix gRPC/protobuf runtime floors"
"""Required-status-check context name added to the version-branches ruleset."""


def _migrate_grpc_ruleset() -> None:
    """Add the grpc check to the 'Protect version branches' ruleset."""
    rule_name = "Protect version branches"
    docs_url = (
        "https://frequenz-floss.github.io/frequenz-repo-config-python/"
        "user-guide/start-a-new-project/configure-github/#rulesets"
    )
    settings_url = get_ruleset_settings_url() or docs_url

    ruleset = get_ruleset(rule_name)
    if ruleset is None:
        manual_step(
            f"The '{rule_name}' GitHub ruleset was not found (or the gh CLI "
            "is not available / the API call failed). "
            "If it should exist for this repository, import it following "
            f"the instructions at {docs_url} and make sure it requires the "
            f"'{_GRPC_REQUIRED_CHECK_CONTEXT}' status check."
        )
        return

    ruleset_id = ruleset.get("id")
    if not isinstance(ruleset_id, int):
        manual_step(
            f"Failed to determine the '{rule_name}' ruleset ID from the "
            f"GitHub API response. Please add the "
            f"'{_GRPC_REQUIRED_CHECK_CONTEXT}' required check manually at "
            f"{settings_url}."
        )
        return

    required_status_checks_found = False
    changed = False
    for rule in ruleset.get("rules", []):
        if rule.get("type") != "required_status_checks":
            continue
        required_status_checks_found = True
        params = rule.setdefault("parameters", {})
        checks = params.setdefault("required_status_checks", [])
        if not isinstance(checks, list):
            manual_step(
                f"The '{rule_name}' ruleset has an unexpected "
                "required_status_checks shape. Please add the "
                f"'{_GRPC_REQUIRED_CHECK_CONTEXT}' required check manually "
                f"at {settings_url}."
            )
            return
        if any(c.get("context") == _GRPC_REQUIRED_CHECK_CONTEXT for c in checks):
            continue
        checks.append(
            {
                "context": _GRPC_REQUIRED_CHECK_CONTEXT,
                "integration_id": 15368,
            }
        )
        changed = True

    if not required_status_checks_found:
        manual_step(
            f"The '{rule_name}' ruleset does not contain a "
            "required_status_checks rule. Please add the "
            f"'{_GRPC_REQUIRED_CHECK_CONTEXT}' required check manually at "
            f"{settings_url}."
        )
        return

    if not changed:
        print(f"  Ruleset '{rule_name}' already requires the grpc check")
        return

    if not update_ruleset(ruleset_id, ruleset):
        manual_step(
            f"Failed to update the '{rule_name}' ruleset via the GitHub "
            f"API. Please add the '{_GRPC_REQUIRED_CHECK_CONTEXT}' "
            f"required check manually at {settings_url}."
        )
        return

    print(
        f"  Updated ruleset '{rule_name}': added "
        f"'{_GRPC_REQUIRED_CHECK_CONTEXT}' required check"
    )


def manual_step(message: str) -> None:
    """Print a manual step message in yellow."""
    _manual_steps.append(message)
    print(f"\033[0;33m>>> {message}\033[0m")


if __name__ == "__main__":
    main()
