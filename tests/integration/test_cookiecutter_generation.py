# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Generation tests for cookiecutter."""

import pathlib
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

    cmd = ". .venv/bin/activate; pip install .[dev-noxfile]; nox"
    print()
    print(f"Running in shell [{cwd}]: {cmd}")
    subprocess.run(cmd, shell=True, cwd=repo_path, check=True)


def _run(cwd: pathlib.Path, *cmd: str) -> subprocess.CompletedProcess[bytes]:
    print()
    print("-" * 80)
    print(f"Running [{cwd}]: {' '.join(cmd)}")
    print()
    return subprocess.run(cmd, cwd=cwd, check=True)
