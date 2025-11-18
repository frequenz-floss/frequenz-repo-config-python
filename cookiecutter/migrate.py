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
from typing import Any, SupportsIndex


def main() -> None:
    """Run the migration steps."""
    # Add a separation line like this one after each migration step.
    print("=" * 72)
    print("Creating Dependabot auto-merge workflow...")
    create_dependabot_auto_merge_workflow()
    print("=" * 72)
    print("Disabling CODEOWNERS review requirement in GitHub ruleset...")
    disable_codeowners_review_requirement()
    print("=" * 72)
    print("Migration script finished. Remember to follow any manual instructions.")
    print("=" * 72)


def create_dependabot_auto_merge_workflow() -> None:
    """Create the Dependabot auto-merge workflow file."""
    workflow_dir = Path(".github") / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    workflow_content = """name: Auto-merge Dependabot PR

on:
  pull_request:

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      - name: Auto-merge Dependabot PR
        uses: >-
          frequenz-floss/dependabot-auto-approve@3cad5f42e79296505473325ac6636be897c8b8a1

        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          dependency-type: 'all'
          auto-merge: 'true'
          merge-method: 'merge'
          add-label: 'tool:auto-merged'
"""

    workflow_file = workflow_dir / "auto-dependabot.yaml"
    workflow_file.write_text(workflow_content, encoding="utf-8")
    print(f"Created/Updated Dependabot auto-merge workflow at {workflow_file}")


def get_default_branch() -> str | None:
    """Get the default branch name from GitHub.

    Returns:
        The default branch name, or None if it cannot be determined.
    """
    try:
        result = subprocess.run(
            ["gh", "api", "repos/:owner/:repo", "--jq", ".default_branch"],
            capture_output=True,
            text=True,
            check=True,
        )
        default_branch = result.stdout.strip()
        print(f"Default branch: {default_branch}")
        return default_branch
    except subprocess.CalledProcessError as e:
        print(f"Failed to get default branch: {e}")
        return None


def find_version_branch_ruleset() -> dict[str, Any] | None:
    """Find the 'Protect version branches' ruleset.

    Returns:
        The ruleset configuration, or None if not found.
    """
    try:
        result = subprocess.run(
            ["gh", "api", "repos/:owner/:repo/rulesets"],
            capture_output=True,
            text=True,
            check=True,
        )
        rulesets = json.loads(result.stdout)

        for ruleset in rulesets:
            if ruleset.get("name") == "Protect version branches":
                return ruleset  # type: ignore[no-any-return]
        return None
    except subprocess.CalledProcessError as e:
        print(f"Failed to fetch rulesets: {e}")
        return None


def update_ruleset(ruleset_id: int, ruleset_config: dict[str, Any]) -> bool:
    """Update a GitHub ruleset configuration.

    Args:
        ruleset_id: The ID of the ruleset to update.
        ruleset_config: The updated ruleset configuration.

    Returns:
        True if the update was successful, False otherwise.
    """
    update_payload = {
        "name": ruleset_config["name"],
        "target": ruleset_config["target"],
        "enforcement": ruleset_config["enforcement"],
        "conditions": ruleset_config["conditions"],
        "rules": ruleset_config["rules"],
    }

    if "bypass_actors" in ruleset_config:
        update_payload["bypass_actors"] = ruleset_config["bypass_actors"]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(update_payload, f, indent=2)
        temp_file = f.name

    try:
        subprocess.run(
            [
                "gh",
                "api",
                "-X",
                "PUT",
                f"repos/:owner/:repo/rulesets/{ruleset_id}",
                "--input",
                temp_file,
            ],
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error updating ruleset: {e}")
        return False
    finally:
        os.unlink(temp_file)


def disable_codeowners_review_requirement() -> None:
    """Disable CODEOWNERS review requirement in GitHub repository ruleset."""
    # Get repository info
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "owner,name"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_info = json.loads(result.stdout)
        org = repo_info["owner"]["login"]
        repo = repo_info["name"]
        ruleset_url = f"https://github.com/{org}/{repo}/settings/rules"
    except subprocess.CalledProcessError:
        ruleset_url = "GitHub repository settings > Rules"

    if get_default_branch() is None:
        manual_step(
            "Failed to get default branch. "
            "Please manually disable the CODEOWNERS review requirement in the "
            f"'Protect version branches' ruleset at: {ruleset_url}"
        )
        return

    version_branch_ruleset = find_version_branch_ruleset()
    if not version_branch_ruleset:
        manual_step(
            "'Protect version branches' ruleset not found. "
            "Please manually disable the CODEOWNERS review requirement at: "
            f"{ruleset_url}"
        )
        return

    ruleset_id = version_branch_ruleset["id"]
    print(f"Found ruleset ID: {ruleset_id}")

    try:
        result = subprocess.run(
            ["gh", "api", f"repos/:owner/:repo/rulesets/{ruleset_id}"],
            capture_output=True,
            text=True,
            check=True,
        )
        ruleset_config = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        manual_step(
            f"Failed to fetch ruleset configuration: {e}. "
            "This action requires admin permissions. "
            f"Please manually disable the CODEOWNERS review requirement at: {ruleset_url}"
        )
        return

    updated = False
    for rule in ruleset_config.get("rules", []):
        if rule.get("type") == "pull_request":
            if rule.get("parameters", {}).get("require_code_owner_review"):
                rule["parameters"]["require_code_owner_review"] = False
                updated = True
                break

    if not updated:
        print("CODEOWNERS review requirement already disabled.")
        return

    if update_ruleset(ruleset_id, ruleset_config):
        print("Successfully disabled CODEOWNERS review requirement in GitHub ruleset.")
    else:
        manual_step(
            "Failed to update GitHub ruleset. This action requires admin permissions. "
            "Please manually disable the CODEOWNERS review requirement in the "
            f"'Protect version branches' ruleset at: {ruleset_url}"
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
