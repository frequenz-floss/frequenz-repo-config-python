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
    subprocess.run(
        [
            "cookiecutter",
            "--no-input",
            cwd / "cookiecutter",
            f"type={repo_type}",
            "name=test",
            "description=Test description",
        ],
        cwd=tmp_path,
        check=True,
    )
    subdirs = list(tmp_path.iterdir())
    assert len(subdirs) == 1
    repo_path = subdirs[0]
    subprocess.run("python3 -m venv .venv".split(), cwd=repo_path, check=True)
    subprocess.run(
        ". .venv/bin/activate; pip install .[dev-noxfile]; nox",
        shell=True,
        cwd=repo_path,
        check=True,
    )
