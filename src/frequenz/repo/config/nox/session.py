# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Predefined nox sessions.

This module defines the predefined nox sessions that are used by the default.
"""

from typing import Any

import nox
from nox.virtualenv import CondaEnv, PassthroughEnv, VirtualEnv

from . import config as _config
from . import util as _util


def uv_install(self: nox.Session, *args: str, **kwargs: Any) -> None:
    """Install invokes `uv pip`_ to install packages inside of the session's
    virtualenv.

    Args:
        self: the nox session.
        args: the packages to install.
        kwargs: additional keyword arguments to pass to the `run` function.

    Raises:
        ValueError: if the session does not have a virtual environment.
    """
    venv = self._runner.venv

    if not isinstance(venv, (CondaEnv, VirtualEnv, PassthroughEnv)):  # pragma: no cover
        raise ValueError("A session without a virtualenv can not install dependencies.")
    if isinstance(venv, PassthroughEnv):
        raise ValueError(
            f"Session {self.name} does not have a virtual environment, so use of"
            " session.install() is no longer allowed since it would modify the"
            " global Python environment. If you're really sure that is what you"
            ' want to do, use session.run("pip", "install", ...) instead.'
        )
    if not args:
        raise ValueError("At least one argument required to install().")

    if self._runner.global_config.no_install and venv._reused:
        return None

    if "silent" not in kwargs:
        kwargs["silent"] = True

    self._run(
        "uv",
        "pip",
        "-v",
        "install",
        "--prerelease=allow",
        *args,
        external=True,
        **kwargs,
    )


nox.Session.install = uv_install


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
