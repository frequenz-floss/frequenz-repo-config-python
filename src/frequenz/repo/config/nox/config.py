# License: MIT
# Copyright © 2022 Frequenz Energy-as-a-Service GmbH

"""TODO."""


import dataclasses
import itertools
from typing import Self

import nox

from . import util

# pylint: disable=fixme
# TODO: to make it more extensible, create one class per defaults type (lib,
# actor, app, api), move defaults to `default_factory` and see if that gets
# generated properly.
#
# If it doesn't work, we can declare each default set separately, either in
# a big nested DEFAULTS dict with the key being the "profile" or several
# DEFAULT_XXX dicts, one per profile.


@dataclasses.dataclass(kw_only=True, slots=True)
class CommandsOptions:
    """TODO."""

    black: list[str] = dataclasses.field(default_factory=lambda: [])
    darglint: list[str] = dataclasses.field(default_factory=lambda: [])
    isort: list[str] = dataclasses.field(default_factory=lambda: [])
    mypy: list[str] = dataclasses.field(default_factory=lambda: [])
    pydocstyle: list[str] = dataclasses.field(default_factory=lambda: [])
    pylint: list[str] = dataclasses.field(default_factory=lambda: [])
    pytest: list[str] = dataclasses.field(default_factory=lambda: [])

    def copy(self) -> Self:
        """Create a new object as a copy of self.

        Returns:
            The copy of self.
        """
        return dataclasses.replace(self)


@dataclasses.dataclass(kw_only=True, slots=True)
class Config:
    """TODO."""

    opts: CommandsOptions = dataclasses.field(default_factory=CommandsOptions)
    sessions: list[str] = dataclasses.field(default_factory=lambda: [])
    source_paths: list[str] = dataclasses.field(default_factory=lambda: [])
    """TODO

    Source paths are inspected for __init__.py files to look for packages,
    it should be any package installed. The path should be the top-level
    directory, as it will be removed when calculating the package name.

    TODO: Get from pyproject.toml
    """

    extra_paths: list[str] = dataclasses.field(default_factory=lambda: [])
    """TODO: A list of path to be used by default and its corresponding package name.

    The package name is needed for mypy, as it takes packages when full import
    checking needs to be done.
    """

    def copy(self, /) -> Self:
        """Create a new object as a copy of self.

        Returns:
            The copy of self.
        """
        return dataclasses.replace(self)

    def path_args(self, session: nox.Session, /) -> list[str]:
        """TODO: Return the file paths to run the checks on.

        If positional arguments are present in the nox session, we use those as the
        file paths, and if not, we use all source files.

        Args:
            session: the nox session.

        Returns:
            the file paths to run the checks on.
        """
        if session.posargs:
            return session.posargs

        return [
            str(p) for p in util.existing_paths(self.source_paths + self.extra_paths)
        ]

    def package_args(self, session: nox.Session, /) -> list[str]:
        """TODO: Return the file paths to run the checks on.

        If positional arguments are present in the nox session, we use those as the
        file paths, and if not, we use all source files.

        Args:
            session: the nox session.

        Returns:
            the file paths to run the checks on.
        """
        if session.posargs:
            return session.posargs

        sources_package_dirs_with_roots = (
            (p, util.find_toplevel_package_dirs(p))
            for p in util.existing_paths(self.source_paths)
        )

        source_packages = (
            util.path_to_package(pkg_path, root=root)
            for root, pkg_paths in sources_package_dirs_with_roots
            for pkg_path in pkg_paths
        )

        extra_packages = (
            util.path_to_package(p) for p in util.existing_paths(self.extra_paths)
        )

        return [*source_packages, *extra_packages]


_config: Config | None = None


def get() -> Config:
    """Get the global configuration object.

    This will raise if `configure()` wasn't called before.

    Returns:
        The global configuration object.
    """
    assert _config is not None, "You must call configure() before using this function"
    return _config


def configure(conf: Config, /) -> None:
    """Configure nox using the provided configuration.

    Args:
        conf: The configuration to use to configure nox.
    """
    global _config  # pylint: disable=global-statement
    _config = conf
    nox.options.sessions = _config.sessions
