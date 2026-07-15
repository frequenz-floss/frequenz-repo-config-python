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
    print("Enabling exhaustive match checks for mypy...")
    migrate_mypy_exhaustive_match()
    print("=" * 72)
    print()

    print("=" * 72)
    print("Removing default `-vv` from pytest addopts...")
    migrate_pytest_addopts_default()
    print("=" * 72)
    print("Removing the dummy DCO merge-queue workflow...")
    migrate_remove_dco_merge_queue_workflow()
    print("=" * 72)
    print("Pinning the DCO check in the 'Protect version branches' ruleset...")
    migrate_protect_version_branches_ruleset()
    print("=" * 72)
    print()

    print("=" * 72)
    print("Updating pinned build dependencies...")
    migrate_build_dependencies()
    print("=" * 72)
    print()

    print("=" * 72)
    print("Enabling asyncio debug mode for pytest...")
    migrate_pytest_asyncio_debug()
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


def _infer_private_repo_from_metadata() -> bool | None:
    """Infer repository privacy from the cookiecutter replay metadata.

    Checks, in order: the ``private_repo`` cookiecutter variable, the
    ``license`` cookiecutter variable, and the ``pyproject.toml`` license
    field.

    Returns:
        ``True`` for private repos, ``False`` for public ones, or ``None``
        when no source provides a usable signal.
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


def migrate_pytest_addopts_default() -> None:
    """Remove the default ``-vv`` from pytest addopts in ``pyproject.toml``.

    Earlier versions of the template set ``addopts = "-vv"`` under
    ``[tool.pytest.ini_options]``.  For projects with many tests this
    default produces a wall of output that makes it hard to see the
    results from other, previous, sessions.  The template no longer ships
    this default; this step removes the matching line from existing
    projects.

    The function is a no-op when ``pyproject.toml`` does not exist, when
    the ``[tool.pytest.ini_options]`` section is missing, or when the
    section has no ``addopts`` line (already migrated).  A manual step is
    emitted when ``addopts`` is present but no longer matches the
    template default, so the maintainer can decide whether to drop
    ``-vv`` from the customized value.
    """
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        manual_step(
            f"{pyproject} was not found. Please remove "
            '`addopts = "-vv"` from `[tool.pytest.ini_options]` manually.'
        )
        return

    try:
        content = pyproject.read_text(encoding="utf-8")
    except OSError as exc:
        manual_step(
            f"Failed to read {pyproject}: {exc}. Please remove "
            '`addopts = "-vv"` from `[tool.pytest.ini_options]` manually.'
        )
        return

    pytest_section_match = re.search(
        r"(?ms)^\[tool\.pytest\.ini_options\]\n.*?(?=^\[|\Z)",
        content,
    )
    if pytest_section_match is None:
        manual_step(
            f"No [tool.pytest.ini_options] section found in {pyproject}. Please remove "
            '`addopts = "-vv"` from `[tool.pytest.ini_options]` manually.'
        )
        return

    pytest_section = pytest_section_match.group(0)
    addopts_match = re.search(r"^addopts\s*=.*$", pytest_section, flags=re.MULTILINE)
    if addopts_match is None:
        print(
            f"  Skipped {pyproject}: no addopts in [tool.pytest.ini_options], "
            "nothiing to remove"
        )
        return

    addopts_line = addopts_match.group(0)
    if addopts_line != 'addopts = "-vv"':
        manual_step(
            f"{pyproject} has a customized `{addopts_line}` line under "
            "[tool.pytest.ini_options]; please drop `-vv` from it manually "
            "if appropriate."
        )
        return

    new_content = content.replace(f"{addopts_line}\n", "", 1)

    try:
        replace_file_atomically(pyproject, new_content)
        print(
            f"  Updated {pyproject}: removed default `-vv` from "
            "[tool.pytest.ini_options]"
        )
    except OSError as exc:
        manual_step(
            f"Failed to update {pyproject}: {exc}. Please remove "
            '`addopts = "-vv"` from `[tool.pytest.ini_options]` manually.'
        )


def migrate_mypy_exhaustive_match() -> None:
    """Enable mypy's ``exhaustive-match`` error code in ``pyproject.toml``.

    The error code reports match statements that leave enum or union variants
    unhandled.  The migration adds it to projects that do not already have an
    ``enable_error_code`` setting.  Projects with a custom setting require a
    manual merge so none of their existing error codes are discarded.
    """
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print(f"  Skipped {pyproject}: file not found")
        return

    try:
        content = pyproject.read_text(encoding="utf-8")
    except OSError as exc:
        manual_step(
            f"Failed to read {pyproject}: {exc}. Please add "
            '`enable_error_code = ["exhaustive-match"]` under `[tool.mypy]` '
            "manually."
        )
        return

    mypy_section_match = re.search(r"(?ms)^\[tool\.mypy\]\n.*?(?=^\[|\Z)", content)
    if mypy_section_match is None:
        manual_step(
            f"{pyproject} has no [tool.mypy] section. Please add "
            '`enable_error_code = ["exhaustive-match"]` manually.'
        )
        return

    mypy_section = mypy_section_match.group(0)
    error_code_match = re.search(
        r"^enable_error_code\s*=.*$", mypy_section, flags=re.MULTILINE
    )
    if error_code_match is not None:
        error_code_line = error_code_match.group(0)
        if "exhaustive-match" in error_code_line:
            print(f"  Skipped {pyproject}: exhaustive-match already enabled")
        else:
            manual_step(
                f"{pyproject} has a customized `{error_code_line}` line under "
                "[tool.mypy]; please add `exhaustive-match` to it manually."
            )
        return

    new_content = content.replace(
        "[tool.mypy]",
        '[tool.mypy]\nenable_error_code = ["exhaustive-match"]',
        1,
    )
    try:
        replace_file_atomically(pyproject, new_content)
        print(f"  Updated {pyproject}: enabled exhaustive-match")
    except OSError as exc:
        manual_step(
            f"Failed to update {pyproject}: {exc}. Please add "
            '`enable_error_code = ["exhaustive-match"]` under `[tool.mypy]` '
            "manually."
        )


def migrate_remove_dco_merge_queue_workflow() -> None:
    """Remove the obsolete dummy DCO merge-queue workflow.

    Older versions of the template shipped
    ``.github/workflows/dco-merge-queue.yml``, a dummy workflow that
    provided a passing ``DCO`` status check on the merge queue because the
    DCO GitHub App did not run on ``merge_group`` events.  The DCO app now
    runs on ``merge_group`` events, so this workflow is obsolete and the
    template no longer ships it.

    The function is a no-op when the workflow file does not exist (already
    migrated).  A manual step is emitted if the file exists but cannot be
    removed.
    """
    workflow = Path(".github/workflows/dco-merge-queue.yml")
    if not workflow.exists():
        print(f"  Skipped {workflow}: file not found")
        return

    try:
        workflow.unlink()
        print(f"  Removed {workflow}")
    except OSError as exc:
        manual_step(f"Failed to remove {workflow}: {exc}. Please delete it manually.")


def migrate_protect_version_branches_ruleset() -> None:
    """Pin the DCO status check in the 'Protect version branches' ruleset.

    Uses the GitHub API (via the ``gh`` CLI) to ensure the ``DCO`` required
    status check in the 'Protect version branches' ruleset is pinned to the
    DCO GitHub App (integration ID ``1861``).  Previously the check accepted
    a ``DCO`` status from any integration, which was needed for the dummy
    merge-queue workflow; now that the DCO app reports on ``merge_group``
    events the check is pinned to the app.

    An existing ``DCO`` check is always pinned in place.  A missing check is
    only added for public repositories; private repositories handle DCO
    manually, so a missing check there is left untouched.  Repository
    visibility is inferred from the cookiecutter replay metadata.

    If the ruleset is already up to date, prints an informational message.
    If the ruleset is not found, the repository visibility cannot be
    determined, or the API call fails, issues a manual-step message.
    """
    rule_name = "Protect version branches"
    dco_integration_id = 1861
    docs_url = (
        "https://frequenz-floss.github.io/frequenz-repo-config-python/"
        "user-guide/start-a-new-project/configure-github/#rulesets"
    )

    ruleset_url = get_ruleset_settings_url() or docs_url

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

    changes: list[str] = []

    for rule in ruleset.get("rules", []):
        if rule.get("type") != "required_status_checks":
            continue
        params = rule.setdefault("parameters", {})
        checks = params.setdefault("required_status_checks", [])
        dco_check = next((c for c in checks if c.get("context") == "DCO"), None)
        if dco_check is not None:
            # Fix an existing DCO check regardless of repo visibility.
            if dco_check.get("integration_id") != dco_integration_id:
                dco_check["integration_id"] = dco_integration_id
                changes.append("pin 'DCO' status check to the DCO app")
            continue
        # A missing DCO check is required for public repos, but private repos
        # handle DCO manually (so it is legitimately absent); only add it when
        # the replay metadata says the repo is public.
        private_repo = _infer_private_repo_from_metadata()
        if private_repo is False:
            checks.append({"context": "DCO", "integration_id": dco_integration_id})
            changes.append("add 'DCO' status check pinned to the DCO app")
        elif private_repo is None:
            manual_step(
                "Could not determine from the cookiecutter replay metadata "
                f"whether this repository is private, so a 'DCO' check was not "
                f"added to the '{rule_name}' ruleset. If this repository is "
                f"public, add a 'DCO' check pinned to the DCO app "
                f"(integration_id {dco_integration_id}) at {ruleset_url}."
            )

    if not changes:
        print(f"  Ruleset '{rule_name}' is already up to date")
        return

    if not update_ruleset(ruleset_id, ruleset):
        manual_step(
            f"Failed to update the '{rule_name}' ruleset via the GitHub API. "
            f"Please apply the following changes manually at {ruleset_url}: "
            + "; ".join(changes)
        )
        return

    print(f"  Updated ruleset '{rule_name}': " + ", ".join(changes))


_BUILD_DEPENDENCIES_PINS = {
    "setuptools": "83.0.0",
    "setuptools_scm[toml]": "10.2.1",
}
"""Build dependencies pinned by the template, mapped to their new versions."""


def migrate_build_dependencies() -> None:
    """Bump the build dependencies pinned by the template in ``pyproject.toml``.

    The template pins its build dependencies to exact versions in
    ``[build-system].requires``, so projects need to be updated whenever
    those pins are bumped in the template.

    In particular ``setuptools-scm`` needs to be at least 10.1 to be able
    to read the version from ``PKG-INFO``.  Older versions delegate that
    fallback to ``vcs-versioning`` without any upper bound, and
    ``vcs-versioning`` 2.x dropped it, which breaks the building of
    distribution packages (the wheel is built from the source
    distribution, where there is no git repository to get the version
    from).

    Dependencies are expected to be pinned as ``"<name> == <version>"``,
    which is what the template generates.  A manual step is emitted when
    a dependency is missing or pinned in any other way, as all projects
    are expected to pin these dependencies exactly.
    """
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        manual_step(
            f"{pyproject} was not found. Please bump the pinned build "
            "dependencies in [build-system] requires manually: "
            + ", ".join(f"{n} to {v}" for n, v in _BUILD_DEPENDENCIES_PINS.items())
            + "."
        )
        return

    try:
        content = pyproject.read_text(encoding="utf-8")
    except OSError as exc:
        manual_step(
            f"Failed to read {pyproject}: {exc}. Please bump the pinned build "
            "dependencies in [build-system] requires manually."
        )
        return

    section_match = re.search(r"(?ms)^\[build-system\]\n.*?(?=^\[|\Z)", content)
    if section_match is None:
        manual_step(
            f"{pyproject} has no [build-system] section. Please bump the "
            "pinned build dependencies manually: "
            + ", ".join(f"{n} to {v}" for n, v in _BUILD_DEPENDENCIES_PINS.items())
            + "."
        )
        return

    section = section_match.group(0)
    updated: list[str] = []
    failed = False

    for name, version in _BUILD_DEPENDENCIES_PINS.items():
        # Only exact pins in the format generated by the template are
        # handled, anything else is left to the user to sort out.
        pin_match = re.search(
            rf'"{re.escape(name)} *== *(?P<version>[0-9][^",<>=!~ ]*) *"', section
        )
        if pin_match is None:
            failed = True
            if re.search(rf'"{re.escape(name)} *[=<>!~]', section):
                manual_step(
                    f"{pyproject} declares `{name}` in [build-system] requires, "
                    f"but not as an exact `{name} == <version>` pin. Please "
                    f"update it to {version} manually."
                )
            else:
                manual_step(
                    f"{pyproject} doesn't declare `{name}` in [build-system] "
                    f"requires. Please add `{name} == {version}` manually."
                )
            continue

        if pin_match.group("version") == version:
            continue

        section = (
            section[: pin_match.start()]
            + f'"{name} == {version}"'
            + section[pin_match.end() :]
        )
        updated.append(f"{name} to {version}")

    if not updated:
        if not failed:
            print(f"  Skipped {pyproject}: build dependencies already up to date")
        return

    new_content = (
        content[: section_match.start()] + section + content[section_match.end() :]
    )

    try:
        replace_file_atomically(pyproject, new_content)
        print(f"  Updated {pyproject}: bumped " + ", ".join(updated))
    except OSError as exc:
        manual_step(
            f"Failed to update {pyproject}: {exc}. Please bump "
            + ", ".join(updated)
            + " in [build-system] requires manually."
        )


def migrate_pytest_asyncio_debug() -> None:
    """Enable asyncio debug mode in pytest when ``pytest-asyncio`` is used.

    The function is a no-op for projects that do not depend on
    ``pytest-asyncio`` or already configure ``asyncio_debug``.  Existing
    values are preserved because they represent an explicit project choice.
    """
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        manual_step(
            f"{pyproject} not found. Please add "
            "`asyncio_debug = true` to `[tool.pytest.ini_options]` manually."
        )
        return

    try:
        content = pyproject.read_text(encoding="utf-8")
    except OSError as exc:
        manual_step(
            f"Failed to read {pyproject}: {exc}. Please add "
            "`asyncio_debug = true` to `[tool.pytest.ini_options]` manually."
        )
        return

    repo_type = read_cookiecutter_str_var("type")
    if repo_type == "api" and "pytest-asyncio" not in content:
        print(f"  Skipped {pyproject}: API project and pytest-asyncio is not used")
        return

    if "pytest-asyncio" not in content:
        manual_step(
            f"{pyproject} does not depend on pytest-asyncio; please make sure this "
            "is OK or add `asyncio_debug = true` to `[tool.pytest.ini_options]` "
            "manually."
        )
        return

    pytest_section_match = re.search(
        r"(?ms)^\[tool\.pytest\.ini_options\]\n.*?(?=^\[|\Z)",
        content,
    )
    if pytest_section_match is None:
        manual_step(
            f"{pyproject} uses pytest-asyncio but has no "
            "`[tool.pytest.ini_options]` section; please add the section and "
            "set `asyncio_debug = true` manually."
        )
        return

    pytest_section = pytest_section_match.group(0)
    asyncio_debug_match = re.search(
        r"^asyncio_debug\s*=.*$", pytest_section, flags=re.MULTILINE
    )
    if asyncio_debug_match is not None:
        print(f"  Skipped {pyproject}: {asyncio_debug_match.group(0)} is already set")
        return

    asyncio_mode_match = re.search(
        r"^asyncio_mode\s*=.*$", pytest_section, flags=re.MULTILINE
    )
    if asyncio_mode_match is None:
        manual_step(
            f"{pyproject} uses pytest-asyncio but has no `asyncio_mode` setting "
            "under `[tool.pytest.ini_options]`; please add "
            "`asyncio_debug = true` there manually."
        )
        return

    new_pytest_section = (
        pytest_section[: asyncio_mode_match.start()]
        + "asyncio_debug = true\n"
        + pytest_section[asyncio_mode_match.start() :]
    )
    new_content = content.replace(pytest_section, new_pytest_section, 1)

    try:
        replace_file_atomically(pyproject, new_content)
        print(
            f"  Updated {pyproject}: enabled asyncio debug mode under "
            "[tool.pytest.ini_options]"
        )
    except OSError as exc:
        manual_step(
            f"Failed to update {pyproject}: {exc}. Please add "
            "`asyncio_debug = true` to `[tool.pytest.ini_options]` manually."
        )


def manual_step(message: str) -> None:
    """Print a manual step message in yellow."""
    _manual_steps.append(message)
    print(f"\033[0;33m>>> {message}\033[0m")


if __name__ == "__main__":
    main()
