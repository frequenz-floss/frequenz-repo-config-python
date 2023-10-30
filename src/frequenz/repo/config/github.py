# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Utilities to work with GitHub.

- [`abort()`][frequenz.repo.config.github.abort] to print an error message using GitHub
    Actions commands and exit.
- [`require_env()`][frequenz.repo.config.github.require_env] to get an environment
    variable or exit with an error if it is not defined.
- [`get_tags()`][frequenz.repo.config.github.get_tags] to get the tags of a repository.
- [`get_branches()`][frequenz.repo.config.github.get_branches] to get the branches of a
    repository.
- [`configure_logging()`][frequenz.repo.config.github.configure_logging] to configure
    logging for GitHub Actions.
"""


import logging
import os
import subprocess
import sys
from typing import NoReturn

import github_action_utils as gha

from . import version

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

    Args:
        name: The name of the environment variable.

    Returns:
        The environment variable.

    Raises:
        ValueError: If the environment variable is not defined.
    """
    value = os.environ.get(name)
    if value is None:
        raise ValueError(f"Environment variable {name!r} is not defined")
    return value


def get_tags(repository: str) -> list[str]:
    """Get the tags of the repository.

    This function uses the `TAGS` environment variable if it is defined. If it is
    not defined, it uses the GitHub `gh` CLI tool to get them. This means the tool
    needs to be properly configured and have at least read access over
    `repository`.

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


def get_branches(repository: str) -> list[str]:
    """Get the branches of the repository.

    This function uses the `BRANCHES` environment variable if it is defined. If it
    is not defined, it uses the GitHub `gh` CLI tool to get them. This means the
    tool needs to be properly configured and have at least read access over
    `repository`.

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


def configure_logging(level: int | None = None) -> None:
    """Configure logging for GitHub Actions.

    The
    [`GitHubActionsFormatter`][frequenz.repo.config.github.GitHubActionsFormatter]
    is used to format the logs, using [GitHub Action
    commands](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions).

    Args:
        level: The logging level to use. If `None`, the level is set to
            `logging.INFO` unless the `RUNNER_DEBUG` environment variable
            is set to `1`, in which case the level is set to
            `logging.DEBUG`.
    """
    # Just for checking it is defined, github_action_utils deals with it automatically.
    require_env("GITHUB_OUTPUT")
    is_debug_run = os.environ.get("RUNNER_DEBUG", None) == "1"
    handler = logging.StreamHandler()
    handler.setFormatter(GitHubActionsFormatter())
    if level is None:
        level = logging.DEBUG if is_debug_run else logging.INFO
    logging.basicConfig(level=level, handlers=[handler])


def get_repo_version_info() -> version.RepoVersionInfo:
    """Get the repository version information.

    This function uses the `GITHUB_REPO`, `GIT_REF`, and `GIT_SHA` environment
    variables to get the repository information. If these variables are not
    defined, it raises a `ValueError`.

    It also uses the `BRANCHES` and `TAGS` environment variables to get the
    branches and tags of the repository. If they are not defined, the GitHub `gh`
    CLI tool is used to get them. This means the tool needs to be properly
    configured and have at least read access over `repository`.

    Returns:
        The repository version information.
    """
    repository = require_env("GITHUB_REPO")
    repo_info = version.RepoVersionInfo(
        ref=require_env("GIT_REF"),
        sha=require_env("GIT_SHA"),
        tags=get_tags(repository),
        branches=get_branches(repository),
    )
    return repo_info
