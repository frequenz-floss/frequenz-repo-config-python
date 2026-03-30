#!/usr/bin/env python3
# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Script to migrate existing projects to new versions of the cookiecutter template.

This script migrates existing projects to new versions of the cookiecutter
template, removing the need to completely regenerate the project from
scratch.

To run it, the simplest way is to fetch it from GitHub and run it directly:

    curl -sSLf https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3 -I

Make sure to replace the `<tag>` to the version you want to migrate to in the URL.

For jumping multiple versions you should run the script multiple times, once
for each version.

And remember to follow any manual instructions for each run.
"""  # noqa: E501

# R0801 is similarity detection, as the template is always similar to the current script
# pylint: disable=too-many-lines, too-many-locals, too-many-branches, R0801

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, SupportsIndex

_manual_steps: list[str] = []  # pylint: disable=invalid-name


_BLACK_MIGRATION_WORKFLOW = (
    """\
# Automatic black formatting migration for Dependabot PRs
#
# When Dependabot upgrades black, this workflow installs the new version
# and runs `black .` so the PR already contains any formatting changes
# introduced by the upgrade, while leaving the PR open for review.
#
# Black uses calendar versioning.  Only the first release of a new calendar
# year may introduce formatting changes (major bump in Dependabot's terms).
# Minor and patch updates within a year keep formatting stable, so they stay
# in the regular Dependabot groups and are auto-merged normally.
#
# The companion auto-dependabot workflow skips major black PRs so they're
# handled exclusively by this migration workflow.
#
# XXX: !!! SECURITY WARNING !!!
# pull_request_target has write access to the repo, and can read secrets.
# This is required because Dependabot PRs are treated as fork PRs: the
# GITHUB_TOKEN is read-only and secrets are unavailable with a plain
# pull_request trigger.  The action mitigates the risk by:
#   - Never executing code from the PR (the migration script is embedded
#     in this workflow file on the base branch, not taken from the PR).
#   - Gating migration steps on github.actor == 'dependabot[bot]'.
#   - Running checkout with persist-credentials: false and isolating
#     push credentials from the migration script environment.
# For more details read:
# https://securitylab.github.com/research/github-actions-preventing-pwn-requests/

name: Black Migration

on:
  merge_group:  # To allow using this as a required check for merging
  pull_request_target:
    types: [opened, synchronize, reopened, labeled, unlabeled]

permissions:
  # Commit reformatted files back to the PR branch.
  contents: write
  # Create and normalize migration state labels.
  issues: write
  # Read/update pull request metadata and comments.
  pull-requests: write

jobs:
  black-migration:
    name: Migrate Black
    # Skip if it was triggered by the merge queue. We only need the workflow to
    # be executed to meet the "Required check" condition for merging, but we
    # don't need to actually run the job, having the job present as Skipped is
    # enough.
    if: |
      github.event_name == 'pull_request_target' &&
      github.actor == 'dependabot[bot]' &&
      contains(github.event.pull_request.title, 'Bump black from ')
    runs-on: ubuntu-24.04
    steps:
      - name: Generate token
        id: create-app-token
        uses: actions/create-github-app-token@f8d387b68d61c58ab83c6c016672934102569859 # v3.0.0
        with:
          app-id: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_ID }}
          private-key: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY }}
          # Push reformatted files to the PR branch.
          permission-contents: write
          # Create and normalize migration state labels.
          permission-issues: write
          # Read/update pull request metadata and labels.
          permission-pull-requests: write
      - name: Migrate
        uses: frequenz-floss/gh-action-dependabot-migrate@"""
    # Broken just to avoid flake8 maximum line length check
    """b389f72f9282346920150a67495efbae450ac07b  # v1.1.0"
        with:
          migration-script: |
            import os
            import subprocess
            import sys

            version = os.environ["MIGRATION_VERSION"].lstrip("v")
            subprocess.run(
                [sys.executable, "-Im", "pip", "install", f"black=={version}"],
                check=True,
            )
            subprocess.run([sys.executable, "-Im", "black", "."], check=True)
          token: ${{ steps.create-app-token.outputs.token }}
          auto-merge-on-changes: "false"
          sign-commits: "true"
          auto-merged-label: "tool:auto-merged"
          migrated-label: "tool:black:migration:executed"
          intervention-pending-label: "tool:black:migration:intervention-pending"
          intervention-done-label: "tool:black:migration:intervention-done"
"""
)


_RELEASE_NOTES_CHECK_REPLACEMENTS = [
    (
        "    permissions:\n      pull-requests: read\n",
        "    permissions:\n"
        "      # Read pull request metadata to evaluate labels and changed files.\n"
        "      pull-requests: read\n",
    ),
    (
        "    runs-on: ubuntu-slim\n    steps:\n",
        "    runs-on: ubuntu-slim\n"
        "    permissions:\n"
        "      # Read pull request metadata to evaluate labels and changed files.\n"
        "      pull-requests: read\n"
        "    steps:\n",
    ),
]


_PRIVATE_REPO_CI_OPTIONAL_PATTERNS = {
    "    permissions:\n      contents: write\n",
    "          python -m frequenz.repo.config.cli.version.mike.info\n",
    "        run: |\n"
    '          mike deploy --update-aliases --title "$TITLE" "$VERSION" '
    "$ALIASES\n",
    "          python -m frequenz.repo.config.cli.version.mike.sort versions.json\n",
}


def main() -> None:
    """Run the migration steps."""
    # Add a separation line like this one after each migration step.
    print("=" * 72)
    print("Updating generated CI workflows...")
    migrate_ci_workflows()
    print("=" * 72)
    print("Updating generated Dependabot workflows...")
    migrate_dependabot_workflows()
    print("=" * 72)
    print("Creating black migration workflow...")
    _migrate_black_migration_workflow()
    print("=" * 72)
    print("Updating auxiliary GitHub workflows...")
    migrate_auxiliary_workflows()
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


def migrate_ci_workflows() -> None:
    """Update the generated CI workflows to the latest template."""
    is_private_repo = has_private_repo_indicators()

    _migrate_workflow_file(
        Path(".github/workflows/ci-pr.yaml"),
        [
            (
                "on:\n  pull_request:\n\nenv:\n",
                "on:\n  pull_request:\n\npermissions:\n"
                "  # Read repository contents for checkout and dependency "
                "resolution only.\n"
                "  contents: read\n\nenv:\n",
            ),
            (
                "        run: |\n"
                "          mike deploy $MIKE_VERSION\n"
                "          mike set-default $MIKE_VERSION\n",
                "        run: |\n"
                "          # mike is installed as a console script, not a "
                "runnable module.\n"
                "          # Run the installed script under isolated mode to "
                "avoid importing from\n"
                "          # the workspace when building docs from checked-out "
                "code.\n"
                '          python -I "$(command -v mike)" deploy "$MIKE_VERSION"\n'
                '          python -I "$(command -v mike)" set-default "$MIKE_VERSION"\n',
            ),
        ],
        description="updated CI pull-request workflow",
    )

    ci_workflow = Path(".github/workflows/ci.yaml")
    private_ci_publish_jobs: list[str] = []
    if is_private_repo and ci_workflow.exists():
        private_ci_publish_jobs = find_ci_publish_jobs(
            _normalize_content(ci_workflow.read_text(encoding="utf-8"))
        )

    _migrate_workflow_file(
        ci_workflow,
        [
            (
                "  workflow_dispatch:\n\nenv:\n",
                "  workflow_dispatch:\n\npermissions:\n"
                "  # Read repository contents for checkout and dependency "
                "resolution only.\n"
                "  contents: read\n\nenv:\n",
            ),
            (
                "    if: always() && needs.nox.result != 'skipped'\n"
                "    runs-on: ubuntu-slim\n"
                "    env:\n",
                "    if: always() && needs.nox.result != 'skipped'\n"
                "    runs-on: ubuntu-slim\n"
                "    # Drop token permissions: this job only checks matrix "
                "status from `needs`.\n"
                "    permissions: {}\n"
                "    env:\n",
            ),
            ("        run: python -m build\n", "        run: python -Im build\n"),
            (
                "        run: python -m pip freeze\n",
                "        run: python -Im pip freeze\n",
            ),
            (
                "    if: always() && needs.test-installation.result != 'skipped'\n"
                "    runs-on: ubuntu-slim\n"
                "    env:\n",
                "    if: always() && needs.test-installation.result != 'skipped'\n"
                "    runs-on: ubuntu-slim\n"
                "    # Drop token permissions: this job only checks matrix "
                "status from `needs`.\n"
                "    permissions: {}\n"
                "    env:\n",
            ),
            (
                "        run: |\n"
                "          mike deploy $MIKE_VERSION\n"
                "          mike set-default $MIKE_VERSION\n",
                "        run: |\n"
                "          # mike is installed as a console script, not a "
                "runnable module.\n"
                "          # Run the installed script under isolated mode to "
                "avoid importing from\n"
                "          # the workspace when building docs from checked-out "
                "code.\n"
                '          python -I "$(command -v mike)" deploy "$MIKE_VERSION"\n'
                '          python -I "$(command -v mike)" set-default "$MIKE_VERSION"\n',
            ),
            (
                "    permissions:\n      contents: write\n",
                "    permissions:\n"
                "      # Push generated documentation updates to the `gh-pages` "
                "branch.\n"
                "      contents: write\n",
            ),
            (
                "          python -m frequenz.repo.config.cli.version.mike.info\n",
                "          python -Im frequenz.repo.config.cli.version.mike.info\n",
            ),
            (
                "        run: |\n"
                '          mike deploy --update-aliases --title "$TITLE" '
                '"$VERSION" $ALIASES\n',
                "        run: |\n"
                "          # Collect aliases into an array to avoid accidental "
                "(or malicious)\n"
                "          # shell injection when passing them to mike.\n"
                "          aliases=()\n"
                '          if test -n "$ALIASES"; then\n'
                '            read -r -a aliases <<<"$ALIASES"\n'
                "          fi\n"
                "          # mike is installed as a console script, not a "
                "runnable module.\n"
                "          # Run the installed script under isolated mode to "
                "avoid importing from\n"
                "          # the workspace when building docs from checked-out "
                "code.\n"
                '          python -I "$(command -v mike)" \\\n'
                '            deploy --update-aliases --title "$TITLE" '
                '"$VERSION" "${aliases[@]}"\n',
            ),
            (
                "          python -m frequenz.repo.config.cli.version.mike.sort "
                "versions.json\n",
                "          python -Im frequenz.repo.config.cli.version.mike.sort "
                "versions.json\n",
            ),
            (
                "    permissions:\n"
                "      # We need write permissions on contents to create GitHub "
                "releases and on\n"
                "      # discussions to create the release announcement in the "
                "discussion forums\n"
                "      contents: write\n"
                "      discussions: write\n",
                "    permissions:\n"
                "      # Create GitHub releases and upload distribution "
                "artifacts.\n"
                "      contents: write\n",
            ),
            (
                "          extra_opts=\n"
                '          if echo "$REF_NAME" | grep -- -; then '
                'extra_opts=" --prerelease"; fi\n'
                "          gh release create \\\n"
                '            -R "$REPOSITORY" \\\n'
                "            --notes-file RELEASE_NOTES.md \\\n"
                "            --generate-notes \\\n"
                "            $extra_opts \\\n"
                "            $REF_NAME \\\n"
                "            dist/*\n",
                "          extra_opts=()\n"
                '          if echo "$REF_NAME" | grep -- -; then '
                "extra_opts+=(--prerelease); fi\n"
                "          gh release create \\\n"
                '            -R "$REPOSITORY" \\\n'
                "            --notes-file RELEASE_NOTES.md \\\n"
                "            --generate-notes \\\n"
                '            "${extra_opts[@]}" \\\n'
                '            "$REF_NAME" \\\n'
                "            dist/*\n",
            ),
        ],
        description="updated main CI workflow",
        ignore_missing_patterns=(
            _PRIVATE_REPO_CI_OPTIONAL_PATTERNS if is_private_repo else None
        ),
    )

    if is_private_repo and private_ci_publish_jobs:
        jobs = ", ".join(f"`{job}`" for job in private_ci_publish_jobs)
        manual_step(
            f"{ci_workflow} still contains {jobs}. This repository appears to be "
            "private, so those publish jobs usually should be removed manually "
            "after the migration, even though the workflow was updated."
        )


def migrate_dependabot_workflows() -> None:
    """Update the generated Dependabot automation workflows."""
    _migrate_workflow_file(
        Path(".github/workflows/auto-dependabot.yaml"),
        [
            (
                "permissions:\n  contents: read\n  pull-requests: write\n",
                "permissions:\n"
                "  # Read repository contents and Dependabot metadata used by "
                "the nested action.\n"
                "  contents: read\n"
                "  # The nested action also uses `github.token` internally for "
                "PR operations.\n"
                "  pull-requests: write\n",
            ),
            (
                "        with:\n"
                "          app-id: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_ID }}\n"
                "          private-key: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY }}\n",
                "        with:\n"
                "          app-id: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_ID }}\n"
                "          private-key: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY }}\n"
                "          # Merge Dependabot PRs.\n"
                "          permission-contents: write\n"
                "          # Create the auto-merged label if it does not exist.\n"
                "          permission-issues: write\n"
                "          # Approve PRs, add labels, and enable auto-merge.\n"
                "          permission-pull-requests: write\n",
            ),
            (
                "      !contains(github.event.pull_request.title, "
                "'the repo-config group')\n"
                "    runs-on:",
                "      !contains(github.event.pull_request.title, "
                "'the repo-config group') &&\n"
                "      !contains(github.event.pull_request.title, "
                "'Bump black from ')\n"
                "    runs-on:",
            ),
        ],
        description="updated Dependabot auto-merge workflow",
    )

    _migrate_workflow_file(
        Path(".github/workflows/repo-config-migration.yaml"),
        [
            (
                "permissions:\n"
                "  contents: write\n"
                "  issues: write\n"
                "  pull-requests: write\n",
                "permissions:\n"
                "  # Commit migration changes back to the PR branch.\n"
                "  contents: write\n"
                "  # Create and normalize migration state labels.\n"
                "  issues: write\n"
                "  # Read/update pull request metadata and comments.\n"
                "  pull-requests: write\n",
            ),
            (
                "        with:\n"
                "          app-id: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_ID }}\n"
                "          private-key: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY }}\n",
                "        with:\n"
                "          app-id: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_ID }}\n"
                "          private-key: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY }}\n"
                "          # Push migration commits to the PR branch.\n"
                "          permission-contents: write\n"
                "          # Manage labels when auto-merging patch-only updates.\n"
                "          permission-issues: write\n"
                "          # Approve pull requests and enable auto-merge.\n"
                "          permission-pull-requests: write\n"
                "          # Allow pushes when migration changes workflow files.\n"
                "          permission-workflows: write\n",
            ),
        ],
        description="updated repo-config migration workflow",
    )


def migrate_auxiliary_workflows() -> None:
    """Update the remaining generated GitHub workflows."""
    _migrate_workflow_file(
        Path(".github/workflows/dco-merge-queue.yml"),
        [
            (
                "on:\n  merge_group:\n\njobs:\n",
                "on:\n  merge_group:\n\n"
                "# Drop all token permissions: this workflow only runs a local "
                "echo command.\n"
                "permissions: {}\n\njobs:\n",
            ),
        ],
        description="updated DCO merge queue workflow",
    )

    _migrate_workflow_file(
        Path(".github/workflows/labeler.yml"),
        [
            (
                "    permissions:\n      contents: read\n      pull-requests: write\n",
                "    permissions:\n"
                "      # Read the labeler configuration from the repository.\n"
                "      contents: read\n"
                "      # Add labels to pull requests.\n"
                "      pull-requests: write\n",
            ),
        ],
        description="updated labeler workflow",
    )

    _migrate_workflow_file(
        Path(".github/workflows/release-notes-check.yml"),
        _RELEASE_NOTES_CHECK_REPLACEMENTS,
        description="updated release notes check workflow",
    )


def _migrate_black_migration_workflow() -> None:
    """Create or replace the black formatting migration workflow."""
    filepath = Path(".github/workflows/black-migration.yaml")
    action = "Updated" if filepath.exists() else "Created"
    replace_file_atomically(filepath, _BLACK_MIGRATION_WORKFLOW)
    print(f"  {action} {filepath}: black formatting migration workflow")


_WORKFLOW_ACTION_PINS: dict[str, str] = {
    "frequenz-floss/gh-action-setup-git": (
        "16952aac3ccc01d27412fe0dea3ea946530dcace # v1.0.0"
    ),
    "actions/checkout": "de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2",
    "yoheimuta/action-protolint": ("e62319541dc5107df5e3a5010acb8987004d3d25 # v1.3.0"),
    "frequenz-floss/gh-action-nox": (
        "e1351cf45e05e85afc1c79ab883e06322892d34c # v1.1.0"
    ),
    "frequenz-floss/gh-action-setup-python-with-deps": (
        "0d0d77eac3b54799f31f25a1060ef2c6ebdf9299 # v1.0.2"
    ),
    "actions/upload-artifact": "bbbca2ddaa5d8feaa63e36b76fdaad77386f024f # v7.0.0",
    "actions/download-artifact": ("3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1"),
    "pypa/gh-action-pypi-publish": (
        "ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e # v1.13.0"
    ),
}


def _normalize_content(content: str) -> str:
    """Normalize content for stable hashing and comparisons."""
    content = content.replace("\r\n", "\n")
    if not content.endswith("\n"):
        content += "\n"
    return content


def _pin_workflow_action_references(content: str) -> str:
    """Pin known action references, but only when they don't use a hash yet."""
    hash_pattern = re.compile(r"[0-9a-f]{40}")

    for action, pin in _WORKFLOW_ACTION_PINS.items():
        pattern = re.compile(
            rf"(^[ \t]*uses:[ \t]+){re.escape(action)}@(?P<ref>[^ \t#\n]+)"
            rf"(?:[ \t]+#.*)?$",
            re.MULTILINE,
        )

        def replace(
            match: re.Match[str], *, action: str = action, pin: str = pin
        ) -> str:
            ref = match.group("ref")
            if hash_pattern.fullmatch(ref):
                return match.group(0)
            return f"{match.group(1)}{action}@{pin}"

        content = pattern.sub(replace, content)

    return content


def _format_missing_patterns(patterns: list[str]) -> str:
    """Format missing replacement patterns for readable error messages."""
    return "\n".join(
        f"Pattern {index}:\n{textwrap.indent(pattern.rstrip(), '    ')}"
        for index, pattern in enumerate(patterns, start=1)
    )


def _apply_idempotent_replacements(
    content: str, replacements: list[tuple[str, str]]
) -> tuple[str, list[str]]:
    """Apply plain-text replacements without duplicating prior migrations."""
    pending_missing_patterns: list[tuple[str, str]] = []

    for old, new in replacements:
        if new in content:
            continue
        if old not in content:
            pending_missing_patterns.append((old, new))
            continue
        content = content.replace(old, new)

    missing_patterns = [
        old for old, new in pending_missing_patterns if new not in content
    ]

    return content, missing_patterns


def _migrate_workflow_file(
    filepath: Path,
    replacements: list[tuple[str, str]],
    *,
    description: str,
    ignore_missing_patterns: set[str] | None = None,
) -> None:
    """Apply text replacements to a generated workflow file.

    The migration is optimized for repositories that still use the generated
    workflow unchanged.  It pins known action references only when they still
    use tags, leaving already hashed references alone so Dependabot can update
    them later.
    """
    if not filepath.exists():
        manual_step(
            f"{filepath} needs updating, but it was not found. Check if the "
            "file was renamed or is missing and update it manually."
        )
        return

    content = _normalize_content(filepath.read_text(encoding="utf-8"))

    updated = _pin_workflow_action_references(content)
    updated, missing_patterns = _apply_idempotent_replacements(updated, replacements)
    if ignore_missing_patterns:
        missing_patterns = [
            pattern
            for pattern in missing_patterns
            if pattern not in ignore_missing_patterns
        ]

    if updated == content:
        if not missing_patterns:
            print(f"  Skipped {filepath}: already has the expected updates")
            return

        manual_step(
            f"Could not find the expected pattern(s) in {filepath}. "
            "Please compare it with the latest template and update it manually.\n"
            f"{_format_missing_patterns(missing_patterns)}"
        )
        return

    replace_file_atomically(filepath, updated)
    print(f"  Updated {filepath}: {description}")

    if missing_patterns:
        manual_step(
            f"Updated {filepath}, but could not find the expected pattern(s). "
            "Please compare it with the latest template and complete the "
            f"remaining changes manually.\n{_format_missing_patterns(missing_patterns)}"
        )


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


def has_private_repo_indicators() -> bool:
    """Return whether the repository appears to be private."""
    github_org = read_cookiecutter_str_var("github_org")
    if github_org is not None and github_org != "frequenz-floss":
        return True

    license_name = read_cookiecutter_str_var("license")
    if license_name == "Proprietary":
        return True

    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        pyproject = _normalize_content(pyproject_path.read_text(encoding="utf-8"))
        if 'license = "LicenseRef-Proprietary"' in pyproject:
            return True

    try:
        stdout = subprocess.check_output(
            ["gh", "repo", "view", "--json", "owner"],
            text=True,
            stderr=subprocess.PIPE,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

    try:
        info: dict[str, Any] = json.loads(stdout)
        owner: str = info["owner"]["login"]
    except (KeyError, TypeError, json.JSONDecodeError):
        return False

    return owner != "frequenz-floss"


def find_ci_publish_jobs(content: str) -> list[str]:
    """Return CI publish job names found in the workflow content."""
    jobs: list[str] = []
    for job_name in ("publish-docs", "publish-to-pypi"):
        if f"\n  {job_name}:\n" in f"\n{content}":
            jobs.append(job_name)
    return jobs


def manual_step(message: str) -> None:
    """Print a manual step message in yellow."""
    _manual_steps.append(message)
    print(f"\033[0;33m>>> {message}\033[0m")


if __name__ == "__main__":
    main()
