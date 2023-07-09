# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Generation tests for cookiecutter."""

import pathlib
import re
import subprocess

import pytest

from frequenz.repo import config


@pytest.mark.integration
@pytest.mark.parametrize("repo_type", [*config.RepositoryType])
def test_generation(tmp_path: pathlib.Path, repo_type: config.RepositoryType) -> None:
    """Test generation of a new repo."""
    cwd = pathlib.Path().cwd()
    repo_path, _ = _generate_repo(repo_type, tmp_path)
    _run(repo_path, "python3", "-m", "venv", ".venv")

    _update_pyproject_repo_config_dep(
        repo_config_path=cwd, repo_type=repo_type, repo_path=repo_path
    )

    cmd = ". .venv/bin/activate; pip install .[dev-noxfile]; nox -e ci_checks_max pytest_min"
    print()
    print(f"Running in shell [{repo_path}]: {cmd}")
    subprocess.run(cmd, shell=True, cwd=repo_path, check=True)


def _generate_repo(
    repo_type: config.RepositoryType,
    tmp_path: pathlib.Path,
    /,
    *,
    capture_output: bool = False,
) -> tuple[pathlib.Path, subprocess.CompletedProcess[bytes]]:
    cwd = pathlib.Path().cwd()
    run_result = _run(
        tmp_path,
        "cookiecutter",
        "--no-input",
        str(cwd / "cookiecutter"),
        f"type={repo_type.value}",
        "name=test",
        "description=Test description",
        capture_output=capture_output,
    )

    subdirs = list(tmp_path.iterdir())
    assert len(subdirs) == 1
    repo_path = subdirs[0]
    return repo_path, run_result


def _run(
    cwd: pathlib.Path, /, *cmd: str, capture_output: bool = False, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    """Run a command in a subprocess."""
    print()
    print("-" * 80)
    print(f"Running [{cwd}]: {' '.join(cmd)}")
    print()
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=capture_output)


def _update_pyproject_repo_config_dep(
    *,
    repo_config_path: pathlib.Path,
    repo_type: config.RepositoryType,
    repo_path: pathlib.Path,
) -> None:
    """Update the repo config dependency in the generated pyproject.toml.

    This is necessary to make sure we are testing the local version of
    `frequenz-repo-config`, otherwise tests will fail because they will be running with
    an older (released) version of `frequenz-repo-config`.

    Args:
        repo_config_path: Path to the local `frequenz-repo-config` repo.
        repo_type: Type of the repo to generate.
        repo_path: Path to the generated repo.
    """
    repo_config_dep = (
        f"frequenz-repo-config[{repo_type.value}] @ file://{repo_config_path}"
    )
    repo_config_dep_re = re.compile(
        rf"""frequenz-repo-config\[{repo_type.value}\][^"]+"""
    )

    with open(repo_path / "pyproject.toml", encoding="utf8") as pyproject_file:
        pyproject_content = pyproject_file.read()

    with open(repo_path / "pyproject.toml", "w", encoding="utf8") as pyproject_file:
        pyproject_file.write(repo_config_dep_re.sub(repo_config_dep, pyproject_content))
