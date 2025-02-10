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
    add_default_pytest_options()
    print("=" * 72)
    migrate_mkdocs_macros()
    print("=" * 72)


def add_default_pytest_options() -> None:
    """Add default pytest options to pyproject.toml."""
    pyproject_toml = Path("pyproject.toml")
    pyproject_toml_content = pyproject_toml.read_text(encoding="utf-8")
    marker = "[tool.pytest.ini_options]\n"
    new_options = (
        "-W=all -Werror -Wdefault::DeprecationWarning "
        "-Wdefault::PendingDeprecationWarning -vv"
    )

    print(f"Adding default pytest options to {pyproject_toml}...")
    if pyproject_toml_content.find(marker) == -1:
        print(
            "Couldn't find the the {marker.strip()} marker in pyproject.toml, skipping update."
        )
        return

    if pyproject_toml_content.find("\naddopts") >= 0:
        print("It looks like some options are already configured, skipping update.")
        manual_step(f"Please consider `{new_options}` if they are not there yet.")
        return

    replace_file_contents_atomically(
        pyproject_toml,
        marker,
        marker + f'addopts = "{new_options}"\n',
    )


def migrate_mkdocs_macros() -> None:
    """Migrate from custom macros.py to standard module."""
    macros_file = Path("docs/_scripts/macros.py")
    mkdocs_yaml = Path("mkdocs.yaml")
    if not mkdocs_yaml.exists():
        mkdocs_yaml = Path("mkdocs.yml")

    known_hashes = {
        "47a991286132471b6cb666577beb89e78c0f5d4975c53f0dcb319c4338a2c3cb",
        "6bb960c72b370ac77918f49d7a35f39c0ddb58fe52cf2d12caa2577098fd8469",
        "7351276ac314955a343bab09d1602e50300887291f841643e9fb79c94acc923c",
        "8fa5f9f3fd928e17f590e3ab056434474633259d615971404db0d2f3034adb62",
        "ba3ff5f1612b3dd22372a8ca95394b8ea468f18dcefc494c73811c8433fcb880",
        "dd32e8759abc43232bb3db5b33c0a7cf8d8442db6135c594968c499d8bae0ce5",
    }

    print("Checking if docs/_scripts/macros.py can be migrated...")

    file_hash = calculate_file_sha256_skip_lines(macros_file, 2)
    if not file_hash:
        return

    if file_hash not in known_hashes:
        manual_step("The macros.py file seems to be customized. You have two options:")
        manual_step("")
        manual_step(
            "1. Switch to the standard module (if you don't have custom macros):"
        )
        manual_step("   a. Update mkdocs.yaml to use the standard module:")
        manual_step(
            '      module_name: docs/_scripts/macros -> modules: ["frequenz.repo.config.mkdocs.mkdocstrings_macros"]'  # noqa: E501
        )
        manual_step("   b. Remove docs/_scripts/macros.py")
        manual_step("")
        manual_step("2. Keep your custom macros but use the standard functionality:")
        manual_step("   a. Update mkdocs.yaml:")
        manual_step("      - Keep using module_name: docs/_scripts/macros")
        manual_step("   b. Update your macros.py to be minimal:")
        manual_step("      ```python")
        manual_step(
            "      from frequenz.repo.config.mkdocs.mkdocstrings_macros import hook_env_with_everything"  # noqa: E501
        )
        manual_step("")
        manual_step("      def define_env(env):")
        manual_step("          # Add your custom variables, filters, and macros here")
        manual_step("          env.variables.my_var = 'Example'")
        manual_step("          env.filters.my_filter = lambda x: x.upper()")
        manual_step("")
        manual_step(
            "          # This must be at the end to enable all standard features"
        )
        manual_step("          hook_env_with_everything(env)")
        manual_step("      ```")
        manual_step("")
        manual_step("See the docs for more details:")
        manual_step(
            "https://frequenz-floss.github.io/frequenz-repo-config-python/v0.12/reference/frequenz/repo/config/mkdocs/mkdocstrings_macros/"  # noqa: E501
        )
        return

    if not mkdocs_yaml.exists():
        print("mkdocs.yaml/yml not found, skipping macros migration")
        return

    content = mkdocs_yaml.read_text(encoding="utf-8")
    if "module_name: docs/_scripts/macros" not in content:
        print("Custom macros configuration not found in mkdocs.yaml")
        return

    print("Updating mkdocs.yaml to use standard module...")
    new_content = content.replace(
        "module_name: docs/_scripts/macros",
        'modules: ["frequenz.repo.config.mkdocs.mkdocstrings_macros"]',
    )
    new_content = new_content.replace(
        "# inside docstrings. See the comment in `docs/_scripts/macros.py` for more\n"
        "  # details\n",
        "# inside docstrings.\n",
    )

    replace_file_contents_atomically(mkdocs_yaml, content, new_content)

    print("Removing docs/_scripts/macros.py...")
    macros_file.unlink()


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


def manual_step(message: str) -> None:
    """Print a manual step message in yellow."""
    print(f"\033[0;33m>>> {message}\033[0m")


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


if __name__ == "__main__":
    main()
