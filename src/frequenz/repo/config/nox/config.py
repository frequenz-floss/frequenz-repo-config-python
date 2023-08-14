# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Configuration utilities for nox.

This module provides utilities to configure the nox sessions. It provides a
`Config` and a `CommandsOptions` class, which are used to configure the nox sessions.

The `get()` function can be used to retrieve the current configuration object
so it can be used when implementing custom nox sessions.

The `configure()` function must be called before `get()` is used.
"""

import dataclasses as _dataclasses
import itertools as _itertools
from typing import Self, assert_never, overload

import nox as _nox

from .._core import RepositoryType
from . import util as _util


@_dataclasses.dataclass(kw_only=True, slots=True)
class CommandsOptions:
    """Command-line options for each command."""

    black: list[str] = _dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `black` command."""

    darglint: list[str] = _dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `darglint` command."""

    isort: list[str] = _dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `isort` command."""

    mypy: list[str] = _dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `mypy` command."""

    pydocstyle: list[str] = _dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `pydocstyle` command."""

    pylint: list[str] = _dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `pylint` command."""

    pytest: list[str] = _dataclasses.field(default_factory=lambda: [])
    """Command-line options for the `pytest` command."""

    def copy(self) -> Self:
        """Create a new object as a copy of self.

        Returns:
            The copy of self.
        """
        return _dataclasses.replace(
            self,
            black=self.black.copy(),
            darglint=self.darglint.copy(),
            isort=self.isort.copy(),
            mypy=self.mypy.copy(),
            pydocstyle=self.pydocstyle.copy(),
            pylint=self.pylint.copy(),
            pytest=self.pytest.copy(),
        )


@_dataclasses.dataclass(kw_only=True, slots=True)
class Config:
    """Configuration for nox sessions."""

    opts: CommandsOptions = _dataclasses.field(default_factory=CommandsOptions)
    """Command-line options for each command used by sessions."""

    sessions: list[str] = _dataclasses.field(default_factory=lambda: [])
    """List of sessions to run."""

    source_paths: list[str] = _dataclasses.field(default_factory=lambda: [])
    """List of paths containing source files that should be analyzed by the sessions.

    Source paths are inspected for `__init__.py` files to look for packages.
    The path should be the top-level directory containing packages that will be
    actually part of the distribution, not development paths, like tests,
    benchmarks, etc.

    This path will be removed when calculating the package name for the found
    packages. `mypy` needs the package name to be able to do full import
    checking.
    """

    extra_paths: list[str] = _dataclasses.field(default_factory=lambda: [])
    """List of extra paths to be analyzed by the sessions.

    These are not inspected for packages, as they are passed verbatim to the
    tools invoked by the sessions.
    """

    def __post_init__(self) -> None:
        """Initialize the configuration object.

        This will add extra paths discovered in config files and other sources.
        """
        for path in _util.discover_paths():
            if path not in self.extra_paths and path not in self.source_paths:
                self.extra_paths.append(path)

    def copy(self, /) -> Self:
        """Create a new object as a copy of self.

        Returns:
            The copy of self.
        """
        return _dataclasses.replace(
            self,
            opts=self.opts.copy(),
            sessions=self.sessions.copy(),
            source_paths=self.source_paths.copy(),
            extra_paths=self.extra_paths.copy(),
        )

    def path_args(self, session: _nox.Session, /) -> list[str]:
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

        return list(
            str(p) for p in _util.existing_paths(self.source_paths + self.extra_paths)
        )

    def package_args(self, session: _nox.Session, /) -> list[str]:
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
            (p, _util.find_toplevel_package_dirs(p))
            for p in _util.existing_paths(self.source_paths)
        )

        source_packages = (
            _util.path_to_package(pkg_path, root=root)
            for root, pkg_paths in sources_package_dirs_with_roots
            for pkg_path in pkg_paths
        )

        extra_packages = (
            _util.path_to_package(p) for p in _util.existing_paths(self.extra_paths)
        )

        return list(
            _util.deduplicate(_itertools.chain(source_packages, extra_packages))
        )


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


@overload
def configure(conf: Config, /, *, import_default_sessions: bool = True) -> None:
    """Configure nox using the provided configuration.

    Args:
        conf: The configuration to use to configure nox.
        import_default_sessions: Whether to import the default sessions or not.
            This is only necessary if you want to avoid using the default provided
            sessions and use your own.
    """


@overload
def configure(
    repo_type: RepositoryType, /, *, import_default_sessions: bool = True
) -> None:
    """Configure nox using the provided repository type.

    Args:
        repo_type: The repository type to use to configure nox.  This will use the
            default configuration in [`frequenz.repo.config.nox.default`][] for that
            type of repository.
        import_default_sessions: Whether to import the default sessions or not.
            This is only necessary if you want to avoid using the default provided
            sessions and use your own.
    """


def configure(
    conf: Config | RepositoryType, /, *, import_default_sessions: bool = True
) -> None:
    """Configure nox using the provided configuration or repository type.

    Args:
        conf: The configuration to use to configure nox, or the repository type to use
            to configure nox.  The later will use the default configuration in
            [`frequenz.repo.config.nox.default`][] for that type of repository.
        import_default_sessions: Whether to import the default sessions or not.
            This is only necessary if you want to avoid using the default provided
            sessions and use your own.
    """
    global _config  # pylint: disable=global-statement

    # We need to make sure sessions are imported, otherwise they won't be visible to nox.
    if import_default_sessions:
        # pylint: disable=import-outside-toplevel,cyclic-import
        from . import session as _

    match conf:
        case Config():
            _config = conf
        case RepositoryType() as repo_type:
            # pylint: disable=import-outside-toplevel,cyclic-import
            from . import default

            match repo_type:
                case RepositoryType.ACTOR:
                    _config = default.actor_config
                case RepositoryType.API:
                    _config = default.api_config
                case RepositoryType.APP:
                    _config = default.app_config
                case RepositoryType.LIB:
                    _config = default.lib_config
                case RepositoryType.MODEL:
                    _config = default.model_config
                case _ as unhandled:
                    assert_never(unhandled)

    _nox.options.sessions = _config.sessions
