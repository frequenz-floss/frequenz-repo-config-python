# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Configuration utilities for nox.

This module provides utilities to configure the nox sessions. It provides a
`Config` and a `CommandsOptions` class, which are used to configure the nox sessions.

The `get()` function can be used to retrieve the current configuration object
so it can be used when implementing custom nox sessions.

The `configure()` function must be called before `get()` is used.
"""

import dataclasses
from typing import Self

import nox

from . import util


@dataclasses.dataclass(kw_only=True, slots=True)
class CommandsOptions:
    """Command-line options for each command."""

    black: list[str] = dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `black` command."""

    darglint: list[str] = dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `darglint` command."""

    isort: list[str] = dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `isort` command."""

    mypy: list[str] = dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `mypy` command."""

    pydocstyle: list[str] = dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `pydocstyle` command."""

    pylint: list[str] = dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `pylint` command."""

    pytest: list[str] = dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `pytest` command."""

    def copy(self) -> Self:
        """Create a new object as a copy of self.

        Returns:
            The copy of self.
        """
        return dataclasses.replace(self)


@dataclasses.dataclass(kw_only=True, slots=True)
class Config:
    """Configuration for nox sessions."""

    opts: CommandsOptions = dataclasses.field(default_factory=CommandsOptions)
    """Command-line options for each command used by sessions."""

    sessions: list[str] = dataclasses.field(default_factory=lambda: [])
    """List of sessions to run."""

    source_paths: list[str] = dataclasses.field(default_factory=lambda: [])
    """List of paths containing source files that should be analyzed by the sessions.

    Source paths are inspected for `__init__.py` files to look for packages.
    The path should be the top-level directory containing packages that will be
    actually part of the distribution, not development paths, like tests,
    benchmarks, etc.

    This path will be removed when calculating the package name for the found
    packages. `mypy` needs the package name to be able to do full import
    checking.
    """

    extra_paths: list[str] = dataclasses.field(default_factory=lambda: [])
    """List of extra paths to be analyzed by the sessions.

    These are not inspected for packages, as they are passed verbatim to the
    tools invoked by the sessions.
    """

    def __post_init__(self) -> None:
        """Initialize the configuration object.

        This will add extra paths discovered in config files and other sources.
        """
        for path in util.discover_paths():
            if path not in self.extra_paths:
                self.extra_paths.append(path)

    def copy(self, /) -> Self:
        """Create a new object as a copy of self.

        Returns:
            The copy of self.
        """
        return dataclasses.replace(self)

    def path_args(self, session: nox.Session, /) -> list[str]:
        """Return the file paths to run the checks on.

        If positional arguments are present in the nox session, those are used
        as the file paths verbatim, and if not, all **existing** `source_paths`
        and `extra_paths` are used.

        Args:
            session: The nox session to use to look for command-line arguments.

        Returns:
            The file paths to run the checks on.
        """
        if session.posargs:
            return session.posargs

        return [
            str(p) for p in util.existing_paths(self.source_paths + self.extra_paths)
        ]

    def package_args(self, session: nox.Session, /) -> list[str]:
        """Return the package names to run the checks on.

        If positional arguments are present in the nox session, those are used
        as the file paths verbatim, and if not, all **existing** `source_paths`
        are searched for python packges by looking for `__init__.py` files.
        `extra_paths` are used as is, only converting the paths to python
        package names (replacing `/` with `.` and removing the suffix `.pyi?`
        if it exists.

        Args:
            session: The nox session to use to look for command-line arguments.

        Returns:
            The package names found in the `source_paths`.
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
"""The global configuration object."""


def get() -> Config:
    """Get the global configuration object.

    This will assert if `configure()` wasn't called before.

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
