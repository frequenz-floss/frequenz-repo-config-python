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

# pylint: disable=too-many-lines, too-many-locals, too-many-branches

import hashlib
import json
import os
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
    print("Fixing repo-config migration merge queue trigger...")
    migrate_repo_config_migration_merge_group_trigger()
    print("=" * 72)
    print("Fixing mkdocstrings-python v2 paths for api repos...")
    migrate_api_mkdocs_mkdocstrings_paths()
    print("=" * 72)
    print("Migrating protolint and publish-to-pypi runners to ubuntu-24.04...")
    migrate_docker_based_runners()
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


def migrate_api_mkdocs_mkdocstrings_paths() -> None:
    """Fix the mkdocstrings paths migration for api repositories."""
    project_type = read_cookiecutter_str_var("type")
    if project_type is None:
        manual_step(
            "Unable to detect the cookiecutter project type from "
            ".cookiecutter-replay.json; if this is an api project and "
            '`mkdocs.yml` still has `paths: ["py"]` nested under '
            "`handlers.python.options`, move it out of `options`."
        )
        return

    if project_type != "api":
        print("  Skipping mkdocs.yml (not an api project)")
        return

    filepath = Path("mkdocs.yml")
    if not filepath.exists():
        manual_step(
            "Unable to find mkdocs.yml; if this project uses mkdocs, "
            'make sure the `paths: ["py"]` config is under '
            "`handlers.python`, not `handlers.python.options`."
        )
        return

    old = '          options:\n            paths: ["py"]'
    new = '          paths: ["py"]\n          options:'
    current_template = (
        '      handlers:\n        paths: ["py"]\n        python:\n          options:'
    )
    content = filepath.read_text(encoding="utf-8")

    if old in content:
        replace_file_contents_atomically(filepath, old, new, count=1)
        print(f"  Updated {filepath}: moved mkdocstrings api paths out of options")
        return

    if new in content or current_template in content:
        print(f"  Skipped {filepath}: mkdocstrings api paths already updated")
        return

    manual_step(
        f"Could not find the api mkdocstrings path pattern in {filepath}. "
        'If `paths: ["py"]` is still nested under `handlers.python.options`, '
        "move it out of `options` according to the latest template."
    )


def migrate_docker_based_runners() -> None:
    """Migrate Docker-based jobs to use ubuntu-24.04 runners.

    The ``protolint`` and ``publish-to-pypi`` jobs need Docker, which is not
    available on ``ubuntu-slim``.  They should therefore run on
    ``ubuntu-24.04`` instead.
    """
    workflows_dir = Path(".github") / "workflows"
    protolint_new = (
        "  protolint:\n"
        "    name: Check proto files with protolint\n"
        "    runs-on: ubuntu-24.04"
    )
    publish_to_pypi_new = (
        '    needs: ["create-github-release"]\n    runs-on: ubuntu-24.04'
    )
    migrations: dict[str, list[dict[str, Any]]] = {}

    protolint_rule = {
        "job": "protolint",
        "required_for": "api repos",
        "job_marker": "  protolint:\n",
        "old": [
            (
                "  protolint:\n"
                "    name: Check proto files with protolint\n"
                "    runs-on: ubuntu-slim"
            ),
            (
                "  protolint:\n"
                "    name: Check proto files with protolint\n"
                "    runs-on: ubuntu-latest"
            ),
        ],
        "new": protolint_new,
    }
    project_type = read_cookiecutter_str_var("type")
    if project_type is None:
        manual_step(
            "Unable to detect the cookiecutter project type from "
            ".cookiecutter-replay.json; cannot determine whether the protolint "
            "runner migration applies."
        )
    elif project_type == "api":
        migrations.setdefault("ci-pr.yaml", []).append(protolint_rule)
        migrations.setdefault("ci.yaml", []).append(protolint_rule)
    else:
        print("  Skipping protolint runner migration (not an api project)")

    github_org = read_cookiecutter_str_var("github_org")
    if github_org is None:
        manual_step(
            "Unable to detect the cookiecutter GitHub organization from "
            ".cookiecutter-replay.json; cannot determine whether the "
            "publish-to-pypi runner migration applies."
        )
    elif github_org == "frequenz-floss":
        migrations.setdefault("ci.yaml", []).append(
            {
                "job": "publish-to-pypi",
                "required_for": "frequenz-floss repos",
                "job_marker": "  publish-to-pypi:\n",
                "old": [
                    ('    needs: ["create-github-release"]\n    runs-on: ubuntu-slim'),
                    (
                        '    needs: ["create-github-release"]\n'
                        "    runs-on: ubuntu-latest"
                    ),
                ],
                "new": publish_to_pypi_new,
            }
        )
    else:
        print("  Skipping publish-to-pypi runner migration (not a frequenz-floss repo)")

    for filename, rules in migrations.items():
        filepath = workflows_dir / filename
        if not filepath.exists():
            for rule in rules:
                manual_step(
                    f"  Expected to find {filepath} for job {rule['job']} in "
                    f"{rule['required_for']}. Please add or update that job to use "
                    "`runs-on: ubuntu-24.04`."
                )
            continue

        for rule in rules:
            job = rule["job"]
            required_for = rule["required_for"]
            job_marker = rule["job_marker"]
            new = rule["new"]
            content = filepath.read_text(encoding="utf-8")

            if job_marker not in content:
                manual_step(
                    f"  Expected to find job {job} in {filepath} for "
                    f"{required_for}. Please update it to use "
                    "`runs-on: ubuntu-24.04`."
                )
                continue

            if new in content:
                print(f"  Skipped {filepath}: runner already up to date for job {job}")
                continue

            for old in rule["old"]:
                if old in content:
                    replace_file_contents_atomically(
                        filepath, old, new, content=content
                    )
                    print(f"  Updated {filepath}: migrated runner for job {job}")
                    break
            else:
                manual_step(
                    f"  Pattern not found in {filepath}: please switch the runner "
                    f"for job {job} to `runs-on: ubuntu-24.04`."
                )


def migrate_repo_config_migration_merge_group_trigger() -> None:
    """Trigger repo-config migration in the merge queue."""
    filepath = Path(".github/workflows/repo-config-migration.yaml")
    if not filepath.exists():
        manual_step(
            "Unable to find .github/workflows/repo-config-migration.yaml; if this "
            "project uses the repo-config migration workflow, update it to trigger "
            "on `merge_group` and skip the job unless the event is "
            "`pull_request_target`."
        )
        return

    content = filepath.read_text(encoding="utf-8")
    old_on = (
        "on:\n"
        "  pull_request_target:\n"
        "    types: [opened, synchronize, reopened, labeled, unlabeled]\n"
    )
    new_on = (
        "on:\n"
        "  merge_group:  # To allow using this as a required check for merging\n"
        "  pull_request_target:\n"
        "    types: [opened, synchronize, reopened, labeled, unlabeled]\n"
    )
    old_if = (
        "    if: contains(github.event.pull_request.title, 'the repo-config group')"
    )
    new_if = (
        "    # Skip if it was triggered by the merge queue. We only need the workflow to\n"
        '    # be executed to meet the "Required check" condition for merging, but we\n'
        "    # don't need to actually run the job, having the job present as Skipped is\n"
        "    # enough.\n"
        "    if: |\n"
        "      github.event_name == 'pull_request_target' &&\n"
        "      contains(github.event.pull_request.title, 'the repo-config group')"
    )

    updated = content
    if old_on in updated:
        updated = updated.replace(old_on, new_on, 1)

    if old_if in updated:
        updated = updated.replace(old_if, new_if, 1)

    if updated != content:
        replace_file_atomically(filepath, updated)
        print(
            "  Updated .github/workflows/repo-config-migration.yaml: added "
            "merge_group trigger"
        )
        return

    if new_on in content and new_if in content:
        print(
            "  Skipped .github/workflows/repo-config-migration.yaml: merge queue "
            "trigger already configured"
        )
        return

    manual_step(
        "Could not find the expected repo-config migration workflow pattern in "
        ".github/workflows/repo-config-migration.yaml. If this repository uses "
        "that workflow, add the `merge_group` trigger and make the job run only "
        "for `pull_request_target` events according to the latest template."
    )


def migrate_protect_version_branches_ruleset() -> None:
    """Update the 'Protect version branches' GitHub ruleset.

    Uses the GitHub API (via ``gh`` CLI) to check whether the
    'Protect version branches' ruleset on the current repository is aligned
    with the current template.  Recent template changes include:

    * Removing the ``copilot_code_review`` rule.

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

    # ── Detect and apply changes in-memory ───────────────────────────────
    changes: list[str] = []
    updated_rules = []

    for rule in ruleset.get("rules", []):
        if rule.get("type") == "copilot_code_review":
            changes.append("remove copilot_code_review")
            continue
        updated_rules.append(rule)

    if not changes:
        print(f"  Ruleset '{rule_name}' is already up to date")
        return

    # ── Push the update ───────────────────────────────────────────────────
    ruleset["rules"] = updated_rules
    if not update_ruleset(ruleset["id"], ruleset):
        manual_step(
            f"Failed to update the '{rule_name}' ruleset via the GitHub API. "
            f"Please apply the following changes manually at {ruleset_url}: "
            + "; ".join(changes)
        )
        return

    print(f"  Updated ruleset '{rule_name}': " + ", ".join(changes))


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


def manual_step(message: str) -> None:
    """Print a manual step message in yellow."""
    _manual_steps.append(message)
    print(f"\033[0;33m>>> {message}\033[0m")


if __name__ == "__main__":
    main()
