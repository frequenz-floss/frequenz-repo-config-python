# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Predefined nox sessions.

This module defines the predefined nox sessions that are used by the default.
"""

import nox

from . import config as _config
from . import util as _util


@nox.session
def ci_checks_max(session: nox.Session) -> None:
    """Run all checks with max dependencies in a single session.

    This is faster than running the checks separately, so it is suitable for CI.

    This does NOT run pytest_min, so that needs to be run separately as well.

    Args:
        session: the nox session.
    """
    session.install("-e", ".[dev]")

    formatting(session, False)
    mypy(session, False)
    pylint(session, False)
    docstrings(session, False)
    pytest_max(session, False)


@nox.session
def formatting(session: nox.Session, install_deps: bool = True) -> None:
    """Check code formatting with black and isort.

    Args:
        session: the nox session.
        install_deps: True if dependencies should be installed.
    """
    if install_deps:
        session.install("-e", ".[dev-formatting]")

    conf = _config.get()
    session.run("black", *conf.opts.black, *conf.path_args(session))
    session.run("isort", *conf.opts.isort, *conf.path_args(session))


@nox.session
def mypy(session: nox.Session, install_deps: bool = True) -> None:
    """Check type hints with mypy.

    Args:
        session: the nox session.
        install_deps: True if dependencies should be installed.
    """
    if install_deps:
        # install the package itself as editable, so that it is possible to do
        # fast local tests with `nox -R -e mypy`.
        session.install("-e", ".[dev-mypy]")

    conf = _config.get()
    pkg_args = _util.flatten(("-p", p) for p in conf.package_args(session))
    session.run("mypy", *conf.opts.mypy, *pkg_args)


@nox.session
def pylint(session: nox.Session, install_deps: bool = True) -> None:
    """Check for code smells with pylint.

    Args:
        session: the nox session.
        install_deps: True if dependencies should be installed.
    """
    if install_deps:
        # install the package itself as editable, so that it is possible to do
        # fast local tests with `nox -R -e pylint`.
        session.install("-e", ".[dev-pylint]")

    conf = _config.get()
    session.run("pylint", *conf.opts.pylint, *conf.path_args(session))


@nox.session
def docstrings(session: nox.Session, install_deps: bool = True) -> None:
    """Check docstring tone with pydocstyle and param descriptions with darglint.

    Args:
        session: the nox session.
        install_deps: True if dependencies should be installed.
    """
    if install_deps:
        session.install("-e", ".[dev-docstrings]")

    conf = _config.get()
    session.run("pydocstyle", *conf.opts.pydocstyle, *conf.path_args(session))

    # Darglint checks that function argument and return values are documented.
    # This is needed only for the `src` dir, so we exclude the other top level
    # dirs that contain code, unless some paths were specified by argument, in
    # which case we use those untouched.
    darglint_paths = session.posargs or filter(
        # pylint: disable=fixme
        # TODO: Make these exclusions configurable
        lambda path: not (path.startswith("tests") or path.startswith("benchmarks")),
        conf.path_args(session),
    )
    session.run("darglint", *conf.opts.darglint, *darglint_paths)


@nox.session
def pytest_max(session: nox.Session, install_deps: bool = True) -> None:
    """Test the code against max dependency versions with pytest.

    Args:
        session: the nox session.
        install_deps: True if dependencies should be installed.
    """
    if install_deps:
        # install the package itself as editable, so that it is possible to do
        # fast local tests with `nox -R -e pytest_max`.
        session.install("-e", ".[dev-pytest]")

    _pytest_impl(session, "max")


@nox.session
def pytest_min(session: nox.Session, install_deps: bool = True) -> None:
    """Test the code against min dependency versions with pytest.

    Args:
        session: the nox session.
        install_deps: True if dependencies should be installed.
    """
    if install_deps:
        # install the package itself as editable, so that it is possible to do
        # fast local tests with `nox -R -e pytest_min`.
        session.install("-e", ".[dev-pytest]", *_util.min_dependencies())

    _pytest_impl(session, "min")


def _pytest_impl(
    session: nox.Session, max_or_min_deps: str  # pylint: disable=unused-argument
) -> None:
    conf = _config.get()
    session.run("pytest", *conf.opts.pytest, *session.posargs)

    # pylint: disable=fixme
    # TODO: Implement coverage reporting, we need to research this a bit and it
    # makes sense to do so when we actually collect the coverage somewhere
    # "--cov=frequenz.sdk",
    # "--cov-report=term",
    # f"--cov-report=html:.htmlcov-{max_or_min_deps}",
