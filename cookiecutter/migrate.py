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

import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any, SupportsIndex

_manual_steps: list[str] = []  # pylint: disable=invalid-name


def main() -> None:
    """Run the migration steps."""
    # Add a separation line like this one after each migration step.
    print("=" * 72)
    print("Fixing the location of the mkdocstrings `paths` key in mkdocs.yml...")
    migrate_mkdocstrings_paths()
    print("=" * 72)
    print("Configuring mypy to check paths instead of packages...")
    migrate_mypy_files()
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


def migrate_mkdocstrings_paths() -> None:
    """Move the mkdocstrings `paths` key under the `python` handler.

    The key belongs to `plugins.mkdocstrings.handlers.python.paths`, but two
    older versions of the template put it elsewhere:

    * Inside `handlers.python.options`, where mkdocstrings ignores it, so the
      source tree is never added to `sys.path`.
    * Directly under `handlers`, where mkdocstrings reads it as a handler name
      and aborts the build with `ModuleNotFoundError: No module named
      'mkdocstrings_handlers.paths'`.

    Both are rewritten to the correct location, and a file that already has it
    there is left untouched. A missing `mkdocs.yml` or a missing `handlers`
    block is reported as a manual step, since every project is expected to have
    both.
    """
    mkdocs_yml = Path("mkdocs.yml")
    handlers_key = "      handlers:"
    python_key = "        python:"
    # Under `handlers` and inside `handlers.python.options`, respectively.
    bad_paths_keys = ("        paths:", "            paths:")

    if not mkdocs_yml.exists():
        manual_step(
            f"{mkdocs_yml} does not exist. Every project should have one; "
            "please check why it is missing and make sure the mkdocstrings "
            "`paths` key sits under `handlers.python`."
        )
        return

    try:
        lines = mkdocs_yml.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError as exc:
        manual_step(
            f"Failed to read {mkdocs_yml}: {exc}. Please make sure the "
            "mkdocstrings `paths` key sits under `handlers.python` manually."
        )
        return

    handlers_index = next(
        (i for i, line in enumerate(lines) if line.startswith(handlers_key)), None
    )
    if handlers_index is None:
        manual_step(
            f"{mkdocs_yml} has no mkdocstrings `handlers` configuration. Every "
            "project should have one; please check why it is missing and make "
            "sure the `paths` key sits under `handlers.python`."
        )
        return

    # The handlers block ends at the first non-blank line indented at most as
    # much as the `handlers:` key itself.
    block_end = len(lines)
    for index in range(handlers_index + 1, len(lines)):
        line = lines[index]
        if line.strip() and len(line) - len(line.lstrip()) <= 6:
            block_end = index
            break
    block = range(handlers_index + 1, block_end)

    bad_index = next(
        (i for i in block if lines[i].startswith(bad_paths_keys)),
        None,
    )
    if bad_index is None:
        print(f"  Skipped {mkdocs_yml}: `paths` key already in the right place")
        return

    python_index = next((i for i in block if lines[i].startswith(python_key)), None)
    if python_index is None:
        manual_step(
            f"{mkdocs_yml} has a misplaced `paths` key but no `python` handler; "
            "please move the key manually."
        )
        return

    paths_value = lines[bad_index].split(":", 1)[1].strip()
    if not paths_value:
        manual_step(
            f"The `paths` key in {mkdocs_yml} spans several lines; please move "
            "it under the `python` handler manually."
        )
        return

    del lines[bad_index]
    if bad_index < python_index:
        python_index -= 1
    lines.insert(python_index + 1, f"          paths: {paths_value}\n")

    try:
        replace_file_atomically(mkdocs_yml, "".join(lines))
        print(f"  Updated {mkdocs_yml}: moved `paths` under the `python` handler")
    except OSError as exc:
        manual_step(
            f"Failed to update {mkdocs_yml}: {exc}. Please move the "
            "mkdocstrings `paths` key under `handlers.python` manually."
        )


def migrate_mypy_files() -> None:
    """Replace the mypy `packages` option with `mypy_path` and `files`.

    With `packages`, a plain `mypy` run only checks the listed packages, so any
    other package in the source directory is never checked, and the nox session
    had to run `mypy` a second time to check tests, docs, etc. Now `mypy` gets
    every path to check from `files`, and the nox session just runs `mypy`.

    The source directory is taken from an existing `mypy_path`, or else it is
    whichever of `src` or `py` contains the configured packages. Other than
    that, only well-known locations are added to `files`, and only if they have
    Python files, as `mypy` fails if a configured path doesn't exist or has no
    Python files. Python files anywhere else are reported as a manual step, as
    only a human can tell whether they should be checked.

    Anything that doesn't fit what the template generates is reported as a
    manual step too.
    """
    pyproject_toml = Path("pyproject.toml")
    if not pyproject_toml.exists():
        manual_step(
            f"{pyproject_toml} does not exist. Every project should have one; "
            "please check why it is missing and configure mypy with `mypy_path` "
            "and `files` instead of `packages` manually."
        )
        return

    try:
        content = pyproject_toml.read_text(encoding="utf-8")
        pyproject = tomllib.loads(content)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        manual_step(
            f"Failed to read {pyproject_toml}: {exc}. Please configure mypy with "
            "`mypy_path` and `files` instead of `packages` manually."
        )
        return

    mypy_config = pyproject.get("tool", {}).get("mypy")
    if mypy_config is None:
        manual_step(
            f"{pyproject_toml} has no `[tool.mypy]` section. Every project should "
            "have one; please check why it is missing and configure mypy with "
            "`mypy_path` and `files`."
        )
        return

    packages = mypy_config.get("packages")
    if "files" in mypy_config:
        if packages is None:
            print(f"  Skipped {pyproject_toml}: mypy already configured with `files`")
            _report_mypy_unchecked_files(mypy_config, _list_python_files())
        else:
            manual_step(
                f"{pyproject_toml} sets both `packages` and `files` for mypy, "
                "which mypy refuses to run with. Please remove `packages` and make "
                "sure `files` lists every path to check."
            )
        return

    if not isinstance(packages, list) or not packages:
        manual_step(
            f"{pyproject_toml} sets neither `packages` nor `files` for mypy. Please "
            "configure `mypy_path` and `files` manually, otherwise `mypy` has "
            "nothing to check."
        )
        return

    mypy_path = mypy_config.get("mypy_path")
    source_dir: str | None = None
    if isinstance(mypy_path, str) and not any(sep in mypy_path for sep in ",:"):
        source_dir = mypy_path
    elif mypy_path is None:
        source_dir = next(
            (
                path
                for path in ("src", "py")
                if all(Path(path, *str(pkg).split(".")).is_dir() for pkg in packages)
            ),
            None,
        )
    if source_dir is None or not all(
        Path(source_dir, *str(pkg).split(".")).is_dir() for pkg in packages
    ):
        manual_step(
            "Couldn't find the source directory containing the mypy packages "
            f"{packages}. Please replace `packages` in {pyproject_toml} with "
            "`mypy_path` (the source directory) and `files` (the source directory "
            "plus tests, docs, noxfile.py, etc.) manually."
        )
        return

    lines = content.splitlines(keepends=True)
    packages_index: int | None = None
    section: str | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            section = stripped
        elif section == "[tool.mypy]" and stripped.startswith("packages"):
            packages_index = index
            break
    if packages_index is None or not lines[packages_index].rstrip().endswith("]"):
        manual_step(
            f"The mypy `packages` option in {pyproject_toml} is not in a single "
            "line; please replace it with `mypy_path` and `files` manually."
        )
        return

    python_files = _list_python_files()
    exclude = _parse_mypy_exclude(mypy_config)
    well_known = ("tests", "pytests", "examples", "benchmarks", "docs", "noxfile.py")
    files = [
        source_dir,
        *(p for p in well_known if _has_mypy_sources(p, python_files, exclude)),
    ]

    new_lines = [
        "# Paths checked when running `mypy` without arguments. They must all exist"
        " and\n",
        "# contain Python files. The nox `mypy` session warns about (and in CI fails"
        " on)\n",
        "# Python files not covered here; use `exclude` for any that shouldn't be"
        " checked.\n",
    ]
    if mypy_path is None:
        new_lines.append(f'mypy_path = "{source_dir}"\n')
    files_toml = ", ".join(f'"{path}"' for path in files)
    new_lines.append(f"files = [{files_toml}]\n")
    lines[packages_index : packages_index + 1] = new_lines

    try:
        replace_file_atomically(pyproject_toml, "".join(lines))
        print(f"  Updated {pyproject_toml}: mypy now checks {files}")
    except OSError as exc:
        manual_step(
            f"Failed to update {pyproject_toml}: {exc}. Please replace the mypy "
            f"`packages` option with `files = {files}` manually."
        )
        return

    _report_mypy_unchecked_files({**mypy_config, "files": files}, python_files)


def _list_python_files() -> list[str] | None:
    """List the Python files in the repository with git.

    Returns:
        The tracked files plus the untracked files that are not ignored, or `None`
            if git can't be run or fails, for example outside a git repository.
    """
    try:
        output = subprocess.check_output(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
            + ["--", "*.py", "*.pyi"],
            text=True,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    # Tracked files deleted from the working tree are listed too
    return [path for path in output.split("\0") if path and Path(path).is_file()]


def _parse_mypy_exclude(mypy_config: dict[str, Any]) -> list[str]:
    """Get the mypy `exclude` regular expressions, parsed like mypy does."""
    exclude = mypy_config.get("exclude", [])
    if isinstance(exclude, str):
        exclude = [exclude]
    return [str(rx).strip() for rx in exclude if str(rx).strip()]


def _parse_mypy_files(mypy_config: dict[str, Any]) -> list[str]:
    """Get the mypy `files` paths, expanded like mypy does, relative to the cwd."""
    files = mypy_config.get("files", [])
    if isinstance(files, str):
        files = files.split(",")
    checked: list[str] = []
    for entry in (str(e).strip() for e in files):
        if not entry:
            continue
        entry = os.path.expandvars(os.path.expanduser(entry))
        for path in glob.glob(entry, recursive=True) or [entry]:
            try:
                path = os.path.relpath(os.path.abspath(path))
            except ValueError:  # On Windows, a path on another drive
                continue
            checked.append(Path(path).as_posix())
    return checked


def _is_covered_by(path: str, entry: str) -> bool:
    """Tell whether mypy checks a file when given a path to check.

    Args:
        path: The file, relative to the current directory, in POSIX form.
        entry: The path given to mypy, in the same form.

    Returns:
        Whether `entry` is `path` itself, or a directory containing `path` in
            which mypy would find it (mypy skips some names when looking for files
            in a directory).
    """
    if path == entry:
        return True
    if entry == ".":
        relative = path
    elif path.startswith(f"{entry}/"):
        relative = path[len(entry) + 1 :]
    else:
        return False
    # mypy skips these when looking for files in a directory
    return not any(
        name in ("__pycache__", "site-packages", "node_modules") or name.startswith(".")
        for name in relative.split("/")
    )


def _is_excluded(path: str, exclude: list[str]) -> bool:
    """Tell whether a file, or any of its parent directories, matches `exclude`."""
    parts = path.split("/")
    candidates = [f"{'/'.join(parts[:i])}/" for i in range(1, len(parts))]
    return any(re.search(rx, c) for rx in exclude for c in [*candidates, path])


def _has_mypy_sources(
    path: str, python_files: list[str] | None, exclude: list[str]
) -> bool:
    """Tell whether mypy would find any Python file to check in a path.

    mypy aborts if a path in `files` doesn't exist, or is a directory where it
    finds no Python files, because they are all in directories it skips, or
    excluded.

    Args:
        path: The path to check, relative to the current directory.
        python_files: The Python files in the repository, as listed by git, or
            `None` if they couldn't be listed, to look for them in `path` instead.
        exclude: The mypy `exclude` regular expressions.

    Returns:
        Whether mypy would find at least one Python file to check in `path`.
    """
    if python_files is None:
        root = Path(path)
        found = [root] if root.is_file() else root.rglob("*.py*")
        python_files = [
            p.as_posix() for p in found if p.is_file() and p.suffix in (".py", ".pyi")
        ]
    # Explicitly listed files are checked even if they match `exclude`
    return any(
        _is_covered_by(file, path) and (file == path or not _is_excluded(file, exclude))
        for file in python_files
    )


def _report_mypy_unchecked_files(
    mypy_config: dict[str, Any], python_files: list[str] | None
) -> None:
    """Report the Python files known to git that mypy won't check as a manual step.

    A file is checked if it is covered by a path in `files` and doesn't match any
    of the `exclude` regular expressions, the same as the nox `mypy` session does:
    both options are parsed like mypy does, `files` entries are expanded (`~`,
    environment variables and globs) and made relative to the current directory,
    and files inside a directory entry are not covered if mypy would skip them
    when looking for files in that directory.
    """
    if python_files is None:
        manual_step(
            "Couldn't list the Python files in the repository with git. Please make "
            "sure the mypy `files` option in pyproject.toml covers all of them, or "
            "`exclude` the ones that shouldn't be checked."
        )
        return

    checked = _parse_mypy_files(mypy_config)
    exclude = _parse_mypy_exclude(mypy_config)

    groups: dict[str, int] = {}
    for path in python_files:
        if any(_is_covered_by(path, entry) for entry in checked):
            continue
        if _is_excluded(path, exclude):
            continue
        group = f"{path.split('/', 1)[0]}/" if "/" in path else path
        groups[group] = groups.get(group, 0) + 1

    if not groups:
        print("  No Python files found outside the paths mypy checks")
        return

    listing = ", ".join(
        (
            f"{group} ({count} file{'s' if count != 1 else ''})"
            if group.endswith("/")
            else group
        )
        for group, count in sorted(groups.items())
    )
    manual_step(
        f"Found Python files that mypy doesn't check: {listing}. Please add them to "
        "the mypy `files` option in pyproject.toml if they should be type-checked, "
        "or to `exclude` if not. Otherwise the nox `mypy` session warns about them, "
        "and fails in CI."
    )


def manual_step(message: str) -> None:
    """Print a manual step message in yellow."""
    _manual_steps.append(message)
    print(f"\033[0;33m>>> {message}\033[0m")


if __name__ == "__main__":
    main()
