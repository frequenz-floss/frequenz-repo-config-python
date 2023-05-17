# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the pyproject.toml file."""

import tomllib

from frequenz.repo.config import RepositoryType

from . import utils


def test_optional_dependencies() -> None:
    """Test that all repository types handled match the defined in RepositoryType."""
    expected = {t.value for t in RepositoryType}

    with open("pyproject.toml", "rb") as pyproject_file:
        pyproject_toml = tomllib.load(pyproject_file)
    defined = {
        k
        for k in pyproject_toml["project"]["optional-dependencies"].keys()
        if k != "dev" and not k.startswith("dev-")
    }
    assert defined == expected, utils.MSG_UNEXPECTED_REPO_TYPES
