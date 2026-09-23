# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Predefined nox sessions.

This module defines the predefined nox sessions that are used by default.
"""

import glob as _glob
import os as _os
import pathlib as _pathlib
import re as _re
import subprocess as _subprocess
import tomllib as _tomllib
from typing import Any

import nox

from . import config as _config
from . import util as _util


@nox.session
def ci_checks_max(session: nox.Session) -> None:
    """Run all checks with max dependencies in a single session.

    This is faster than running the checks separately, so it is suitable for CI.

    This does NOT run [`pytest_min`][..pytest_min], so that needs to be run separately as
    well.

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

    The paths to check are taken from the `files` option in the `tool.mypy`
    section of `pyproject.toml`, so running `mypy` directly checks the same paths
    as this session. The session fails if the option is missing, as `mypy` would
    otherwise check only part of the code, or nothing at all.

    After running `mypy`, the session warns about the Python files in the
    repository that `mypy` doesn't check, so they can be added to `files`, or to
    `exclude` if they shouldn't be checked. The files are listed with `git`,
    tracked plus untracked but not ignored. When running in CI (the `CI`
    environment variable is set to anything but an empty string, `0`, `false`,
    `no` or `off`, case-insensitive), the warning is an error instead, unless
    [`mypy_unchecked_files_error_in_ci`][...config.Config.mypy_unchecked_files_error_in_ci]
    is disabled.

    Positional arguments are passed to `mypy` as the paths to check instead, and
    skip all the checks above.

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

    mypy_config = _read_mypy_config()
    if "files" not in mypy_config:
        session.error(
            "mypy has no `files` configured, so it wouldn't check all the code. "
            "Please set `mypy_path` and `files` in the `tool.mypy` section of "
            "`pyproject.toml` (and remove `packages`), for example by running the "
            "frequenz-repo-config migration script."
        )

    session.run("mypy", *conf.opts.mypy)

    _check_mypy_unchecked_files(session, conf, mypy_config)


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


def _read_mypy_config() -> dict[str, Any]:
    """Read the mypy configuration from `pyproject.toml`.

    Returns:
        The `tool.mypy` section, or an empty dictionary if there is none.
    """
    with open("pyproject.toml", "rb") as toml_file:
        data = _tomllib.load(toml_file)
    mypy_config: dict[str, Any] = data.get("tool", {}).get("mypy", {})
    return mypy_config


def _check_mypy_unchecked_files(
    session: nox.Session, conf: _config.Config, mypy_config: dict[str, Any]
) -> None:
    """Warn about, or fail on, Python files mypy doesn't check.

    Args:
        session: the nox session.
        conf: the nox configuration.
        mypy_config: the `tool.mypy` section of `pyproject.toml`.
    """
    try:
        unchecked = _find_mypy_unchecked_files(mypy_config)
    except (OSError, _subprocess.CalledProcessError) as exc:
        session.warn(
            f"Couldn't list the Python files in the repository with git ({exc}), "
            "so files mypy doesn't check can't be detected."
        )
        return

    if not unchecked:
        return

    max_listed = conf.mypy_unchecked_files_max_listed
    listed = ", ".join(unchecked[:max_listed])
    if len(unchecked) > max_listed:
        listed += f" and {len(unchecked) - max_listed} more"
    message = (
        f"Found {len(unchecked)} Python file(s) mypy doesn't check: {listed}. "
        "Add them to `files` in the `tool.mypy` section of `pyproject.toml` if they "
        "should be type-checked, or to `exclude` if not"
    )

    if _in_ci() and conf.mypy_unchecked_files_error_in_ci:
        session.error(message)  # nox adds a trailing period
    session.warn(f"{message}.")


def _in_ci() -> bool:
    """Tell whether the session runs in CI.

    Returns:
        Whether the `CI` environment variable is set to a non-empty value other
            than `0`, `false`, `no` or `off` (case-insensitive).
    """
    value = _os.environ.get("CI", "").strip().lower()
    return value not in ("", "0", "false", "no", "off")


def _find_mypy_unchecked_files(mypy_config: dict[str, Any]) -> list[str]:
    """Find the Python files in the repository that mypy doesn't check.

    The files are listed with git, tracked plus untracked but not ignored, so
    virtual environments, build outputs, etc. are skipped. A file is checked if it
    is covered by a path in the `files` option and doesn't match any of the
    `exclude` regular expressions, both parsed like mypy does.

    `files` entries are expanded like mypy does (`~`, environment variables and
    globs) and made relative to the current directory. A file is covered by an
    entry naming it, or by a directory entry containing it, unless a directory
    below the entry, or the file itself, is named `__pycache__`, `site-packages`
    or `node_modules`, or starts with `.`, as mypy skips those when looking for
    files in a directory.

    `exclude` is matched like mypy does, against the relative path of the file and
    of each of its parent directories (with a trailing `/`).

    If git can't be run, or fails (for example outside a git repository), the
    `OSError` or `subprocess.CalledProcessError` raised by `subprocess.run()`
    propagates.

    Args:
        mypy_config: the `tool.mypy` section of `pyproject.toml`.

    Returns:
        The paths of the Python files mypy doesn't check, sorted.
    """
    output = _subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
        + ["--", "*.py", "*.pyi"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    files = mypy_config.get("files", [])
    if isinstance(files, str):
        files = files.split(",")
    exclude = mypy_config.get("exclude", [])
    if isinstance(exclude, str):
        exclude = [exclude]
    exclude = [rx.strip() for rx in exclude if rx.strip()]

    checked: list[str] = []
    for entry in (e.strip() for e in files):
        if not entry:
            continue
        entry = _os.path.expandvars(_os.path.expanduser(entry))
        for path in _glob.glob(entry, recursive=True) or [entry]:
            try:
                path = _os.path.relpath(_os.path.abspath(path))
            except ValueError:  # On Windows, a path on another drive
                continue
            checked.append(_pathlib.Path(path).as_posix())

    unchecked: list[str] = []
    for path in sorted(set(output.split("\0"))):
        # Tracked files deleted from the working tree are listed too
        if not path or not _pathlib.Path(path).is_file():
            continue
        if any(_is_covered_by(path, entry) for entry in checked):
            continue
        parts = path.split("/")
        candidates = [f"{'/'.join(parts[:i])}/" for i in range(1, len(parts))]
        candidates.append(path)
        if any(_re.search(rx, c) for rx in exclude for c in candidates):
            continue
        unchecked.append(path)
    return unchecked


def _is_covered_by(path: str, entry: str) -> bool:
    """Tell whether mypy checks a file when given a path to check.

    Args:
        path: the relative path of the file, in POSIX form.
        entry: the relative path to check, in POSIX form.

    Returns:
        Whether `path` is `entry`, or is inside `entry` and mypy would find it when
            looking for files in that directory.
    """
    if path == entry:
        return True
    if entry == ".":
        relative = path
    elif path.startswith(f"{entry}/"):
        relative = path[len(entry) + 1 :]
    else:
        return False
    return not any(
        name in ("__pycache__", "site-packages", "node_modules") or name.startswith(".")
        for name in relative.split("/")
    )
