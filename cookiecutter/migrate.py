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
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import SupportsIndex

_manual_steps: list[str] = []  # pylint: disable=invalid-name


def main() -> None:
    """Run the migration steps."""
    # Add a separation line like this one after each migration step.
    print("=" * 72)
    print("Migrating workflows to use ubuntu-slim runner for lightweight jobs...")
    migrate_to_ubuntu_slim()
    print("=" * 72)
    print("Migrating pyproject license metadata to SPDX format...")
    migrate_pyproject_license()
    print("=" * 72)
    print("Adding flake8-datetimez plugin to dev-flake8 dependencies...")
    migrate_add_flake8_datetimez()
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
