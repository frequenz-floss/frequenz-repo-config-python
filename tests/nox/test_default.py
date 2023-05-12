# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the nox.default module."""

from frequenz.repo import config
from frequenz.repo.config.nox import default

from .. import utils


def test_all_repository_types_are_handled() -> None:
    """Test that all repository types handled match the defined in RepositoryType."""
    expected = {
        *{f"{repo_type.value}_config" for repo_type in config.RepositoryType},
        *{f"{repo_type.value}_command_options" for repo_type in config.RepositoryType},
        "common_config",
        "common_command_options",
    }

    defined = {
        f
        for f in dir(default)
        if not f.startswith("_")
        and (f.endswith("_config") or f.endswith("_command_options"))
    }
    assert defined == expected, utils.MSG_UNEXPECTED_REPO_TYPES
