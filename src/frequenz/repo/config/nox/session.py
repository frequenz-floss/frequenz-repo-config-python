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
    flake8(session, False)
    mypy(session, False)
    pylint(session, False)
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

    # If we get CLI options, we run mypy on those, but still passing the
    # configured options (they can be overridden by the CLI options).
    if session.posargs:
        session.run("mypy", *conf.opts.mypy, *session.posargs)
        return

    # We separate running the mypy checks into two runs, one is the default, as
    # configured in `pyproject.toml`, which should run against the sources.
    session.run("mypy", *conf.opts.mypy)

    # The second run checks development files, like tests, benchmarks, etc.
    # This is an attempt to minimize mypy internal errors.
    session.run(
        "mypy", *conf.opts.mypy, *conf.path_args(session, include_sources=False)
    )


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
def flake8(session: nox.Session, install_deps: bool = True) -> None:
    """Check for common errors and in particular documentation format and style.

    Args:
        session: the nox session.
        install_deps: True if dependencies should be installed.
    """
    if install_deps:
        session.install("-e", ".[dev-flake8]")

    conf = _config.get()
    session.run("flake8", *conf.opts.flake8, *conf.path_args(session))


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
