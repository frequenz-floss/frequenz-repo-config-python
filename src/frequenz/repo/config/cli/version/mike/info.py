# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Command-line tool to get the current `mike` version information of a repository.

For now this tool is designed to be used in GitHub Actions workflows, but is is possible
to use it in other environments as well. To do so the `gh` tool should be properly
configured and have at least read-access to the repository, and the following environment
variables should be set:

- `GITHUB_REPO`: The repository to get the version information of (e.g.
  `frequenz-floss/frequenz-sdk-python`).
- `GIT_REF`: The git reference to get the version information of (e.g.
  `refs/heads/v1.x.x`).
- `GIT_SHA`: The git sha to get the version information of (e.g.
  `84df6ad1d9990d7afd47a9f8e8a386702b09eba0`).
- `TAGS`: The tags of the repository (e.g. `v1.0.0 v1.0.1`).
- `BRANCHES`: The branches of the repository (e.g. `v1.x.x v2.x.x`).
- `GITHUB_OUTPUT`: The output variable to set the version information to (e.g.
  `/dev/stdout`).
"""

import logging
import os
import subprocess
import sys
from typing import NoReturn

import github_action_utils as gha

from .... import version
from ....mkdocs import mike

_logger = logging.getLogger(__name__)


class GitHubActionsFormatter(logging.Formatter):
    """A formatter for GitHub Actions."""

    level_mapping: dict[int, str] = {
        logging.CRITICAL: "error",
        logging.ERROR: "error",
        logging.WARNING: "warning",
        logging.INFO: "notice",
        logging.DEBUG: "debug",
    }
    """The mapping from logging levels to GitHub Actions levels."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the record using GitHub Actions commands.

        Args:
            record: The record to format.

        Returns:
            The formatted record.
        """
        github_level = self.level_mapping.get(record.levelno, "notice")
        github_command = f"::{github_level}::{record.getMessage()}"
        return github_command


def _output_gha_vars(mike_version: mike.MikeVersionInfo) -> None:
    """Output mike version information as GitHub Action variables."""
    _logger.debug("Outputting mike version information as GitHub Action variables:")
    _logger.debug("  title: %r", mike_version.title)
    _logger.debug("  version: %r", mike_version.version)
    _logger.debug("  aliases: %r", " ".join(mike_version.aliases))

    gha.set_output("title", mike_version.title)
    gha.set_output("version", mike_version.version)
    gha.set_output("aliases", " ".join(mike_version.aliases))


def abort(  # pylint: disable=too-many-arguments
    message: str,
    title: str | None = None,
    file: str | None = None,
    col: int | None = None,
    end_column: int | None = None,
    line: int | None = None,
    end_line: int | None = None,
    use_subprocess: bool = False,
    error_code: int = 1,
) -> NoReturn:
    """Print an error message using GitHub Actions commands and exit.

    Args:
        message: The message of the error.
        title: The title of the error.
        file: The file where the error occurred.
        col: The column where the error occurred.
        end_column: The end column where the error occurred.
        line: The line where the error occurred.
        end_line: The end line where the error occurred.
        use_subprocess: Whether to use subprocess to print the error.
        error_code: The error code to exit with.
    """
    gha.error(
        message,
        title=title,
        file=file,
        col=col,
        end_column=end_column,
        line=line,
        end_line=end_line,
        use_subprocess=use_subprocess,
    )
    sys.exit(error_code)


def require_env(name: str) -> str:
    """Get the environment variable.

    Exit with an error if the environment variable is not defined.

    Args:
        name: The name of the environment variable.

    Returns:
        The environment variable.
    """
    value = os.environ.get(name)
    if value is None:
        abort(f"{name} is not defined", title="Environment variable not defined")
    return value


def _get_tags(repository: str) -> list[str]:
    """Get the tags of the repository.

    Args:
        repository: The repository to get the tags of.

    Returns:
        The tags of the repository.
    """
    tags_str: list[str]
    if env_tags := os.environ.get("TAGS", None):
        tags_str = env_tags.split()
    else:
        tags_str = (
            subprocess.check_output(
                [
                    "gh",
                    "api",
                    "-q",
                    ".[].name",
                    "-H",
                    "Accept: application/vnd.github+json",
                    "-H",
                    "X-GitHub-Api-Version: 2022-11-28",
                    f"/repos/{repository}/tags",
                ]
            )
            .decode("utf-8")
            .splitlines()
        )

    _logger.debug("Got tags: %r", tags_str)
    return tags_str


def _get_branches(repository: str) -> list[str]:
    """Get the branches of the repository.

    Args:
        repository: The repository to get the branches of.

    Returns:
        The branches of the repository.
    """
    branches_str: list[str]
    if env_branches := os.environ.get("BRANCHES", None):
        branches_str = env_branches.split()
    else:
        branches_str = (
            subprocess.check_output(
                [
                    "gh",
                    "api",
                    "-q",
                    ".[].name",
                    "-H",
                    "Accept: application/vnd.github+json",
                    "-H",
                    "X-GitHub-Api-Version: 2022-11-28",
                    f"/repos/{repository}/branches",
                ]
            )
            .decode("utf-8")
            .splitlines()
        )
    _logger.debug("Got branches: %r", branches_str)
    return branches_str


def _configure_logging(is_debug_run: bool) -> None:
    """Configure logging for GitHub Actions.

    Args:
        is_debug_run: Whether the run is a debug run.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(GitHubActionsFormatter())
    level = logging.DEBUG if is_debug_run else logging.INFO
    logging.basicConfig(level=level, handlers=[handler])


def main() -> None:
    """Output mike version variables for GitHub Actions."""
    is_debug_run = os.environ.get("RUNNER_DEBUG", None) == "1"
    _configure_logging(is_debug_run)

    repository = require_env("GITHUB_REPO")
    repo_info = version.RepoVersionInfo(
        ref=require_env("GIT_REF"),
        sha=require_env("GIT_SHA"),
        tags=_get_tags(repository),
        branches=_get_branches(repository),
    )
    # Just for checking it is defined, github_action_utils deals with it automatically.
    require_env("GITHUB_OUTPUT")

    try:
        mike_version = mike.build_mike_version(repo_info)
    except ValueError as error:
        abort(f"{error}.", title="Documentation was not published")

    _output_gha_vars(mike_version)


if __name__ == "__main__":
    main()
