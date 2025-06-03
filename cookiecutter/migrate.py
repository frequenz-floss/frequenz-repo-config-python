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
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Final, SupportsIndex


def main() -> None:
    """Run the migration steps."""
    # Add a separation line like this one after each migration step.
    print("=" * 72)
    migrate_filterwarnings(Path("pyproject.toml"))
    print(
        "Renaming the deprecated mkdocstrings `import` to `inventories` in `mkdocs.yml`..."
    )
    print("=" * 72)
    replace_file_contents_atomically(
        "mkdocs.yml", "          import:", "          inventories:"
    )
    print("=" * 72)
    print("Migration script finished. Remember to follow any manual instructions.")
    print("=" * 72)


# pylint: disable-next=too-many-locals,too-many-statements,too-many-branches
def migrate_filterwarnings(path: Path) -> None:
    """Migrate the filterwarnings configuration in pyproject.toml files."""
    print(f"Migrating from pytest addopts to filterwarnings in {path}...")
    # Patterns to identify and clean existing addopts flags
    addopts_re: Final = re.compile(r'^(\s*)addopts\s*=\s*"(.*)"')
    filterwarnings_re: Final = re.compile(r"^(\s*)filterwarnings\s*=\s*(.*)")
    w_flag_re: Final = re.compile(r"^-W=?(.*)$")
    unwanted_flags: Final = {
        "-W=all",
        "-Werror",
        "-Wdefault::DeprecationWarning",
        "-Wdefault::PendingDeprecationWarning",
    }

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    new_lines: list[str] = []
    modified = False
    addopts_found = False
    has_filterwarnings = False
    has_w_flags = False
    w_flags: list[str] = []

    for line in lines:
        filterwarnings_match = filterwarnings_re.match(line)
        if filterwarnings_match:
            has_filterwarnings = True
        addopts_match = addopts_re.match(line)
        if addopts_match and not modified:
            addopts_found = True
            indent, inner = addopts_match.group(1), addopts_match.group(2)
            tokens = inner.split()
            remaining_tokens: list[str] = []
            extra_specs: list[str] = []

            for tok in tokens:
                if tok in unwanted_flags:
                    # Discard it; it will be replaced by base_specs
                    continue

                w_match = w_flag_re.match(tok)
                if w_match:
                    w_flags.append(tok)
                    has_w_flags = True
                    spec = w_match.group(1)
                    if spec:
                        # Convert this -W... into a filterwarnings spec
                        extra_specs.append(spec)
                else:
                    # Keep any non -W token
                    remaining_tokens.append(tok)

            # Base filterwarnings specs to replace unwanted flags
            base_specs = map(
                str.strip,
                r"""
                "error",
                "once::DeprecationWarning",
                "once::PendingDeprecationWarning",
                # We ignore warnings about protobuf gencode version being one version older
                # than the current version, as this is supported by protobuf, and we expect to
                # have such cases. If we go too far, we will get a proper error anyways.
                # We use a raw string (single quotes) to avoid the need to escape special
                # characters as this is a regex.
                'ignore:Protobuf gencode version .*exactly one major version older.*:UserWarning',
                """.strip().splitlines(),
            )

            # Rebuild addopts line without unwanted flags
            new_addopts_value = " ".join(remaining_tokens)
            new_lines.append(f'{indent}addopts = "{new_addopts_value}"\n')

            # Build the filterwarnings block
            new_lines.append(f"{indent}filterwarnings = [\n")
            # This is fine, indent is defined only once, so even if it is a closure
            # bound late, the value will always be the same.
            # pylint: disable-next=cell-var-from-loop
            new_lines.extend(map(lambda s: f"{indent}  {s}\n", base_specs))
            for spec in extra_specs:
                new_lines.append(f'{indent}  "{spec}",\n')
            new_lines.append(f"{indent}]\n")

            modified = True
        else:
            new_lines.append(line)

    if modified and not has_filterwarnings:
        print(f"Updated {path} to use filterwarnings.")
        path.write_text("".join(new_lines), encoding="utf-8")
        return

    if has_filterwarnings and not has_w_flags:
        print(
            f"The file {path} already has a `filterwarnings` section and has no "
            "-W flags in `addopts`, it is probably already migrated."
        )
    elif has_filterwarnings and has_w_flags:
        print(
            f"The file {path} already has a `filterwarnings` section, but also "
            f"has -W flags in `addopts` ({' '.join(w_flags)!r}), it looks like "
            "it is half-migrated, you should probably migrate it manually. Avoid using -W "
            "flags in `addopts` if there is a `filterwarnings` section."
        )
    if not addopts_found:
        print(f"No 'addopts' found in {path}.")

    manual_step(
        f"No changes done to {path}. "
        "Please double check no manual steps are required."
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
