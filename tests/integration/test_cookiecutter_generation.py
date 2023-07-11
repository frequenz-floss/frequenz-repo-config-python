# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Generation tests for cookiecutter."""

import pathlib
import re
import subprocess

import pytest

from frequenz.repo import config


@pytest.mark.integration
@pytest.mark.parametrize("repo_type", [t.value for t in config.RepositoryType])
def test_generation(tmp_path: pathlib.Path, repo_type: str) -> None:
    """Test generation of a new repo."""
    cwd = pathlib.Path().cwd()
    _run(
        tmp_path,
        "cookiecutter",
        "--no-input",
        str(cwd / "cookiecutter"),
        f"type={repo_type}",
        "name=test",
        "description=Test description",
    )

    subdirs = list(tmp_path.iterdir())
    assert len(subdirs) == 1
    repo_path = subdirs[0]
    _run(repo_path, "python3", "-m", "venv", ".venv")

    _update_pyproject_repo_config_dep(
        repo_config_path=cwd, repo_type=repo_type, repo_path=repo_path
    )

    cmd = ". .venv/bin/activate; pip install .[dev-noxfile]; nox -e ci_checks_max pytest_min"
    print()
    print(f"Running in shell [{repo_path}]: {cmd}")
    subprocess.run(cmd, shell=True, cwd=repo_path, check=True)


def _run(cwd: pathlib.Path, *cmd: str) -> subprocess.CompletedProcess[bytes]:
    print()
    print("-" * 80)
    print(f"Running [{cwd}]: {' '.join(cmd)}")
    print()
    return subprocess.run(cmd, cwd=cwd, check=True)


def _update_pyproject_repo_config_dep(
    *, repo_config_path: pathlib.Path, repo_type: str, repo_path: pathlib.Path
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
    repo_config_dep = f"frequenz-repo-config[{repo_type}] @ file://{repo_config_path}"
    repo_config_dep_re = re.compile(rf"""frequenz-repo-config\[{repo_type}\][^"]+""")

    with open(repo_path / "pyproject.toml", encoding="utf8") as pyproject_file:
        pyproject_content = pyproject_file.read()

    with open(repo_path / "pyproject.toml", "w", encoding="utf8") as pyproject_file:
        pyproject_file.write(repo_config_dep_re.sub(repo_config_dep, pyproject_content))
