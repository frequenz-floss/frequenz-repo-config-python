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

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import SupportsIndex


def main() -> None:
    """Run the migration steps."""
    # Add a separation line like this one after each migration step.
    print("=" * 72)
    print("Migrating workflows to use ubuntu-slim runner for lightweight jobs...")
    migrate_to_ubuntu_slim()
    print("=" * 72)
    print("Migration script finished. Remember to follow any manual instructions.")
    print("=" * 72)


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
            {
                "job": "publish-to-pypi",
                "old": '    needs: ["create-github-release"]\n    runs-on: ubuntu-24.04',
                "new": '    needs: ["create-github-release"]\n    runs-on: ubuntu-slim',
            },
        ],
        "auto-dependabot.yaml": [
            {
                "job": "auto-merge",
                "old": (
                    "  auto-merge:\n"
                    "    if: github.actor == 'dependabot[bot]'\n"
                    "    runs-on: ubuntu-latest"
                ),
                "new": (
                    "  auto-merge:\n"
                    "    if: github.actor == 'dependabot[bot]'\n"
                    "    runs-on: ubuntu-slim"
                ),
            }
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


def apply_patch(patch_content: str) -> None:
    """Apply a patch using the patch utility."""
    subprocess.run(["patch", "-p1"], input=patch_content.encode(), check=True)


def replace_file_contents_atomically(  # noqa; DOC501
    filepath: str | Path,
    old: str,
    new: str,
    count: SupportsIndex = -1,
    *,
    content: str | None = None,
) -> None:
    """Replace a file atomically with new content.

    Args:
        filepath: The path to the file to replace.
        old: The string to replace.
        new: The string to replace it with.
        count: The maximum number of occurrences to replace. If negative, all occurrences are
            replaced.
        content: The content to replace. If not provided, the file is read from disk.

    The replacement is done atomically by writing to a temporary file and
    then moving it to the target location.
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    if content is None:
        content = filepath.read_text(encoding="utf-8")

    content = content.replace(old, new, count)

    # Create temporary file in the same directory to ensure atomic move
    tmp_dir = filepath.parent

    # pylint: disable-next=consider-using-with
    tmp = tempfile.NamedTemporaryFile(mode="w", dir=tmp_dir, delete=False)

    try:
        # Copy original file permissions
        st = os.stat(filepath)

        # Write the new content
        tmp.write(content)

        # Ensure all data is written to disk
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()

        # Copy original file permissions to the new file
        os.chmod(tmp.name, st.st_mode)

        # Perform atomic replace
        os.rename(tmp.name, filepath)

    except BaseException:
        # Clean up the temporary file in case of errors
        tmp.close()
        os.unlink(tmp.name)
        raise


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
    print(f"\033[0;33m>>> {message}\033[0m")


if __name__ == "__main__":
    main()
