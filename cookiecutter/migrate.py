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
import os
import subprocess
import tempfile
from pathlib import Path
from typing import SupportsIndex


def main() -> None:
    """Run the migration steps."""
    # Add a separation line like this one after each migration step.
    print("=" * 72)
    regroup_dependabot()
    print("=" * 72)
    print("Migration script finished. Remember to follow any manual instructions.")
    print("=" * 72)


def regroup_dependabot() -> None:
    """Use new dependabot groups to separate dependencies that break often."""
    print("Using new dependabot groups to separate dependencies that break often...")
    # Dependabot configuration file
    dependabot_file = Path(".github/dependabot.yml")

    # Skip if the file doesn't exist
    if not dependabot_file.exists():
        manual_step(
            "Dependabot configuration file not found, not excluding "
            "frequenz-repo-config from group updates. Please consider adding a "
            "dependabot configuration file."
        )
        return

    dependabot_content = dependabot_file.read_text(encoding="utf-8")

    new_groups = """\
    # We group patch updates as they should always work.
    # We also group minor updates, as it works too for most libraries,
    # typically except libraries that don't have a stable release yet (v0.x.x
    # branch), so we make some exceptions for them.
    # Major updates and dependencies excluded by the above groups are still
    # managed, but they'll create one PR per dependency, as breakage is
    # expected, so it might need manual intervention.
    # Finally, we group some dependencies that are related to each other, and
    # usually need to be updated together.
    groups:
      patch:
        update-types:
          - "patch"
        exclude-patterns:
          # pydoclint has shipped breaking changes in patch updates often
          - "pydoclint"
      minor:
        update-types:
          - "minor"
        exclude-patterns:
          - "async-solipsism"
          - "frequenz-repo-config*"
          - "markdown-callouts"
          - "mkdocs-gen-files"
          - "mkdocs-literate-nav"
          - "mkdocstrings*"
          - "pydoclint"
          - "pytest-asyncio"
      # We group repo-config updates as it uses optional dependencies that are
      # considered different dependencies otherwise, and will create one PR for
      # each if we don't group them.
      repo-config:
        patterns:
          - "frequenz-repo-config*"
      mkdocstrings:
        patterns:
          - "mkdocstrings*"
"""

    marker = "    open-pull-requests-limit: 10"
    if marker not in dependabot_content:
        manual_step(
            f"Could not file marker ({marker!r}) in {dependabot_file}, "
            "can't update automatically. Please consider using these new groups "
            "in the dependabot configuration file:"
        )
        return

    text_to_replace = ""
    found_marker = False
    for line in dependabot_content.splitlines():
        if line == marker:
            found_marker = True
            continue
        if not found_marker:
            continue
        if line == "" and found_marker:
            break
        text_to_replace += line + "\n"

    if not text_to_replace:
        manual_step(
            "Could not find the text to replace with the new depenndabot "
            "groups. Please consider using these new groups in the dependabot "
            "configuration file:"
        )
        return

    replace_file_contents_atomically(
        dependabot_file,
        text_to_replace,
        new_groups,
        count=1,
        content=dependabot_content,
    )


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
