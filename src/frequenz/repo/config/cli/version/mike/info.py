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

import github_action_utils as gha

from .... import github
from ....mkdocs import mike

_logger = logging.getLogger(__name__)


def _output_gha_vars(mike_version: mike.MikeVersionInfo) -> None:
    """Output mike version information as GitHub Action variables."""
    _logger.debug("Outputting mike version information as GitHub Action variables:")
    _logger.debug("  title: %r", mike_version.title)
    _logger.debug("  version: %r", mike_version.version)
    _logger.debug("  aliases: %r", " ".join(mike_version.aliases))

    gha.set_output("title", mike_version.title)
    gha.set_output("version", mike_version.version)
    gha.set_output("aliases", " ".join(mike_version.aliases))


def main() -> None:
    """Output mike version variables for GitHub Actions."""
    github.configure_logging()

    try:
        mike_version = mike.build_mike_version(github.get_repo_version_info())
    except ValueError as error:
        gha.warning(
            f"{error}.", title="Could not determine the version information for `mike`"
        )
        return

    _output_gha_vars(mike_version)


if __name__ == "__main__":
    main()
