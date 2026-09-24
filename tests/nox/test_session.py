# License: MIT
# Copyright © 2026 Frequenz Energy-as-a-Service GmbH

"""Tests for the nox.session module."""

import pathlib
import subprocess
from unittest import mock

import pytest

from frequenz.repo.config.nox import config, session


class _SessionError(Exception):
    """Raised by the fake `session.error()`, like nox does."""


def _session_error(*args: object) -> None:
    raise _SessionError(*args)


@pytest.fixture
def nox_session(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> mock.MagicMock:
    """Provide a fake nox session running in an empty temporary git repository."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CI", raising=False)
    subprocess.run(["git", "init", "-q"], check=True)
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        config, "_CONFIG", config.Config(opts=config.CommandsOptions(mypy=["--opt"]))
    )
    fake_session = mock.MagicMock()
    fake_session.posargs = []
    fake_session.error.side_effect = _session_error
    return fake_session


def _write_mypy_config(mypy_config: str) -> None:
    pathlib.Path("pyproject.toml").write_text(
        f"[tool.mypy]\n{mypy_config}\n", encoding="utf-8"
    )


def _create_files(*paths: str) -> None:
    for path in map(pathlib.Path, paths):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()


def _warnings(nox_session: mock.MagicMock) -> list[str]:
    return [str(call.args[0]) for call in nox_session.warn.call_args_list]


def test_mypy_runs_once_with_configured_files(nox_session: mock.MagicMock) -> None:
    """Test mypy runs once, without paths, when `files` is configured."""
    _write_mypy_config('mypy_path = "src"\nfiles = ["src", "tests"]')
    _create_files("src/pkg/__init__.py", "tests/test_pkg.py")

    session.mypy(nox_session, False)

    nox_session.error.assert_not_called()
    nox_session.warn.assert_not_called()
    nox_session.run.assert_called_once_with("mypy", "--opt")


@pytest.mark.parametrize(
    "mypy_config",
    ['packages = ["frequenz.test"]', "strict = true"],
    ids=["packages", "nothing"],
)
def test_mypy_fails_without_configured_files(
    nox_session: mock.MagicMock, mypy_config: str
) -> None:
    """Test mypy fails, without running, when `files` is not configured."""
    _write_mypy_config(mypy_config)

    with pytest.raises(_SessionError):
        session.mypy(nox_session, False)

    nox_session.run.assert_not_called()


def test_mypy_fails_without_mypy_section(nox_session: mock.MagicMock) -> None:
    """Test mypy fails, without running, when there is no mypy configuration."""
    with pytest.raises(_SessionError):
        session.mypy(nox_session, False)

    nox_session.run.assert_not_called()


def test_mypy_posargs_override_files(nox_session: mock.MagicMock) -> None:
    """Test positional arguments are checked even if `files` is not configured."""
    _write_mypy_config('packages = ["frequenz.test"]')
    _create_files("stray.py")
    nox_session.posargs = ["tests/test_a.py"]

    session.mypy(nox_session, False)

    nox_session.error.assert_not_called()
    nox_session.warn.assert_not_called()
    nox_session.run.assert_called_once_with("mypy", "--opt", "tests/test_a.py")


def test_mypy_warns_about_unchecked_files(nox_session: mock.MagicMock) -> None:
    """Test mypy warns about Python files not covered by `files`."""
    _write_mypy_config('files = ["src", "noxfile.py"]')
    _create_files(
        "noxfile.py",
        "src/pkg/__init__.py",
        "src_old/pkg.py",
        "stray.py",
        "stubs/pkg.pyi",
        "tests/test_pkg.py",
        "tests/README.md",
    )

    session.mypy(nox_session, False)

    nox_session.error.assert_not_called()
    nox_session.run.assert_called_once_with("mypy", "--opt")
    assert _warnings(nox_session) == [
        "Found 4 Python file(s) mypy doesn't check: src_old/pkg.py, stray.py, "
        "stubs/pkg.pyi, tests/test_pkg.py. Add them to `files` in the `tool.mypy` "
        "section of `pyproject.toml` if they should be type-checked, or to "
        "`exclude` if not."
    ]


def test_mypy_ignores_excluded_and_git_ignored_files(
    nox_session: mock.MagicMock,
) -> None:
    """Test files matching `exclude`, or ignored by git, are not reported."""
    _write_mypy_config(
        "files = ['src/**/*.py', './tests/']\n"
        "exclude = ['^tools/', '/generated/', 'legacy\\.py$']"
    )
    pathlib.Path(".gitignore").write_text("build/\n", encoding="utf-8")
    _create_files(
        "src/pkg/__init__.py",
        "tests/test_pkg.py",
        "tools/gen.py",
        "docs/generated/api.py",
        "scripts/legacy.py",
        "build/lib/pkg/__init__.py",
    )

    session.mypy(nox_session, False)

    nox_session.error.assert_not_called()
    nox_session.warn.assert_not_called()


def test_mypy_expands_files_like_mypy(
    nox_session: mock.MagicMock,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test `files` entries are expanded and made relative like mypy does."""
    monkeypatch.setenv("PROJ", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path.parent))
    _write_mypy_config(
        f"files = ['$PROJ/src', '~/{tmp_path.name}/tests', '{tmp_path}/noxfile.py']"
    )
    _create_files("src/pkg/__init__.py", "tests/test_pkg.py", "noxfile.py", "stray.py")

    session.mypy(nox_session, False)

    nox_session.error.assert_not_called()
    (warning,) = _warnings(nox_session)
    assert "Found 1 Python file(s) mypy doesn't check: stray.py." in warning


@pytest.mark.parametrize(
    "files", ['"src, tests,"', '"src,, tests"', '["src", "", " tests "]']
)
def test_mypy_ignores_empty_files_entries(
    nox_session: mock.MagicMock, files: str
) -> None:
    """Test empty `files` entries don't cover the whole repository."""
    _write_mypy_config(f"files = {files}")
    _create_files("src/pkg.py", "tests/test_pkg.py", "stray.py")

    session.mypy(nox_session, False)

    (warning,) = _warnings(nox_session)
    assert "Found 1 Python file(s) mypy doesn't check: stray.py." in warning


@pytest.mark.parametrize(
    "exclude", ['""', '"  "', '["", " "]', '"^tools/ "', '[" ^tools/", ""]']
)
def test_mypy_parses_exclude_like_mypy(
    nox_session: mock.MagicMock, exclude: str
) -> None:
    """Test `exclude` items are stripped, and empty ones don't exclude everything."""
    _write_mypy_config(f'files = ["src"]\nexclude = {exclude}')
    _create_files("src/pkg.py", "tools/gen.py", "stray.py")

    session.mypy(nox_session, False)

    (warning,) = _warnings(nox_session)
    expected = "stray.py" if "tools" in exclude else "stray.py, tools/gen.py"
    assert f"mypy doesn't check: {expected}." in warning


def test_mypy_reports_files_mypy_skips_in_directories(
    nox_session: mock.MagicMock,
) -> None:
    """Test files in directories mypy skips when recursing are reported."""
    _write_mypy_config(
        "files = ['src', '.github/cookiecutter-migrate.template.py', '.ci']"
    )
    _create_files(
        ".ci/check.py",
        ".github/cookiecutter-migrate.template.py",
        ".github/other.py",
        "src/.hidden.py",
        "src/.hidden/h.py",
        "src/__pycache__/c.py",
        "src/node_modules/n.py",
        "src/pkg/__init__.py",
        "src/pkg/site-packages/s.py",
    )
    # Track them, so a global gitignore (with `__pycache__`, for example) can't hide them
    subprocess.run(["git", "add", "-f", "."], check=True)

    session.mypy(nox_session, False)

    (warning,) = _warnings(nox_session)
    assert (
        "Found 6 Python file(s) mypy doesn't check: .github/other.py, src/.hidden.py, "
        "src/.hidden/h.py, src/__pycache__/c.py, src/node_modules/n.py and 1 more."
    ) in warning


def test_mypy_limits_listed_unchecked_files(nox_session: mock.MagicMock) -> None:
    """Test only the configured number of unchecked files are listed."""
    config.get().mypy_unchecked_files_max_listed = 2
    _write_mypy_config('files = ["src"]')
    _create_files("src/pkg.py", "a.py", "b.py", "c.py")

    session.mypy(nox_session, False)

    (warning,) = _warnings(nox_session)
    assert "Found 3 Python file(s) mypy doesn't check: a.py, b.py and 1 more." in (
        warning
    )


@pytest.mark.parametrize("ci", ["true", "1", "on", "woodpecker", " TRUE "])
def test_mypy_fails_on_unchecked_files_in_ci(
    nox_session: mock.MagicMock, monkeypatch: pytest.MonkeyPatch, ci: str
) -> None:
    """Test unchecked files make the session fail in CI."""
    monkeypatch.setenv("CI", ci)
    _write_mypy_config('files = ["src"]')
    _create_files("src/pkg.py", "stray.py")

    with pytest.raises(_SessionError, match="stray.py"):
        session.mypy(nox_session, False)

    nox_session.run.assert_called_once_with("mypy", "--opt")


@pytest.mark.parametrize("ci", ["", "0", "false", "no", "off", "FALSE", " Off "])
def test_mypy_warns_on_unchecked_files_if_ci_is_disabled(
    nox_session: mock.MagicMock, monkeypatch: pytest.MonkeyPatch, ci: str
) -> None:
    """Test unchecked files only warn if `CI` is set to a false value."""
    monkeypatch.setenv("CI", ci)
    _write_mypy_config('files = ["src"]')
    _create_files("src/pkg.py", "stray.py")

    session.mypy(nox_session, False)

    nox_session.error.assert_not_called()
    (warning,) = _warnings(nox_session)
    assert "stray.py" in warning


def test_mypy_warns_on_unchecked_files_in_ci_if_disabled(
    nox_session: mock.MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test unchecked files only warn in CI if failing is disabled."""
    monkeypatch.setenv("CI", "true")
    config.get().mypy_unchecked_files_error_in_ci = False
    _write_mypy_config('files = ["src"]')
    _create_files("src/pkg.py", "stray.py")

    session.mypy(nox_session, False)

    nox_session.error.assert_not_called()
    (warning,) = _warnings(nox_session)
    assert "stray.py" in warning


def test_mypy_warns_if_not_a_git_repository(
    nox_session: mock.MagicMock, tmp_path: pathlib.Path
) -> None:
    """Test the unchecked files check is skipped with a warning without git."""
    (tmp_path / ".git").rename(tmp_path / "not-git")
    _write_mypy_config('files = ["src"]')
    _create_files("src/pkg.py", "stray.py")

    session.mypy(nox_session, False)

    nox_session.error.assert_not_called()
    (warning,) = _warnings(nox_session)
    assert warning.startswith("Couldn't list the Python files")
