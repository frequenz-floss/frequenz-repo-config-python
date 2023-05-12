# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the core module."""

from frequenz.repo.config import RepositoryType

from . import utils


def test_repository_type_doesnt_have_new_types() -> None:
    """Test that `RepositoryType` doesn't have new types."""
    expected = {
        "actor",
        "api",
        "app",
        "lib",
        "model",
    }
    defined = {t.value for t in RepositoryType}
    assert defined == expected, utils.MSG_UNEXPECTED_REPO_TYPES
