# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Generation tests for cookiecutter."""

import os
import pathlib
import re
import shutil
import subprocess

import pytest

from frequenz.repo import config

UPDATE_GOLDEN: bool = os.environ.get("UPDATE_GOLDEN", "").lower() in (
    "1",
    "true",
    "yes",
)
"""Set to True to update the golden files.

After setting to True you need to run the tests once to update the golden files.

Make sure to review the changes before committing them and setting this back to False.
"""


@pytest.mark.integration
@pytest.mark.parametrize("repo_type", [*config.RepositoryType])
def test_golden(
    tmp_path: pathlib.Path,
    repo_type: config.RepositoryType,
    request: pytest.FixtureRequest,
) -> None:
    """Test generation of a new repo comparing it to a golden tree."""
    env = os.environ.copy()
    env.update(
        # Make sure file sorting, dates, etc. are deterministic.
        LANG="C",
        LANGUAGE="C",
        LC_ALL="C",
        # Signal to the cookiecutter template that it is running in a golden test, so
        # some flaky outputs can be disabled.
        GOLDEN_TEST="1",
    )

    cwd = pathlib.Path().cwd()
    golden_path = (
        cwd
        / "tests_golden"
        / request.path.relative_to(cwd / "tests").with_suffix("")
        / repo_type.value
    )

    generated_repo_path, run_result = _generate_repo(
        repo_type, tmp_path, capture_output=True, env=env
    )
    stdout, stderr = _filter_generation_output(run_result)
    _assert_golden_file(golden_path, "cookiecutter-stdout", stdout)
    _assert_golden_file(golden_path, "cookiecutter-stderr", stderr)
    _assert_golden_tree(
        generated_repo_path=generated_repo_path,
        golden_tree=golden_path / generated_repo_path.name,
    )


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
    env: dict[str, str] | None = None,
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
        env=env,
    )

    subdirs = list(tmp_path.iterdir())
    assert len(subdirs) == 1
    repo_path = subdirs[0]
    return repo_path, run_result


def _run(
    cwd: pathlib.Path,
    /,
    *cmd: str,
    capture_output: bool = False,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Run a command in a subprocess."""
    print()
    print("-" * 80)
    print(f"Running [{cwd}]: {' '.join(cmd)}")
    print()
    return subprocess.run(
        cmd, cwd=cwd, check=check, capture_output=capture_output, env=env
    )


def _read_golden_file(golden_path: pathlib.Path, name: str) -> str:
    """Read a golden file.

    File names will be appended with ".txt".

    Args:
        golden_path: The path to the directory containing the golden files.
        name: The name of the golden file.

    Returns:
        The contents of the file.
    """
    with open(
        golden_path / f"{name}.txt", "r", encoding="utf8", errors="replace"
    ) as golden_file:
        return golden_file.read()


def _write_golden_file(golden_path: pathlib.Path, name: str, contents: str) -> int:
    """Write a golden file.

    File names will be appended with ".txt".

    Args:
        golden_path: The path to the directory containing the golden files.
        name: The name of the golden file.

    Returns:
        The number of bytes written.
    """
    golden_path.mkdir(parents=True, exist_ok=True)
    with open(
        golden_path / f"{name}.txt", "w", encoding="utf8", errors="replace"
    ) as golden_file:
        return golden_file.write(contents)


def _assert_golden_file(
    golden_path: pathlib.Path,
    name: str,
    new_result: str | bytes | subprocess.CompletedProcess[bytes],
) -> None:
    if isinstance(new_result, subprocess.CompletedProcess):
        _assert_golden_file(golden_path, f"{name}-stdout", new_result.stdout)
        _assert_golden_file(golden_path, f"{name}-stderr", new_result.stderr)
        return

    if isinstance(new_result, bytes):
        new_result = new_result.decode("utf-8", "replace")
    if UPDATE_GOLDEN:
        _write_golden_file(golden_path, name, new_result)
    else:
        assert new_result == _read_golden_file(golden_path, name)


def _read_golden_tree(
    *, generated_repo_path: pathlib.Path, golden_tree: pathlib.Path
) -> subprocess.CompletedProcess[bytes]:
    """Read a golden tree.

    The `diff` command is used to compare the generated tree with the golden tree.

    Args:
        generated_repo_path: The path to the generated repository tree.
        golden_tree: The path to the golden tree.

    Returns:
        The result of the `diff` command.
    """
    return _run(
        generated_repo_path,
        "diff",
        "-ru",
        str(generated_repo_path),
        str(golden_tree),
        check=False,
        capture_output=True,
    )


def _write_golden_tree(
    *, generated_repo_path: pathlib.Path, golden_tree: pathlib.Path
) -> None:
    """Write a golden tree.

    Replace all files in the golden tree with the files from the generated tree.

    Args:
        generated_repo_path: The path to the generated repository tree.
        golden_tree: The path to the golden tree.
    """
    if golden_tree.exists():
        shutil.rmtree(golden_tree)
    shutil.copytree(generated_repo_path, golden_tree, dirs_exist_ok=True)


def _assert_golden_tree(
    *, generated_repo_path: pathlib.Path, golden_tree: pathlib.Path
) -> None:
    if UPDATE_GOLDEN:
        _write_golden_tree(
            generated_repo_path=generated_repo_path, golden_tree=golden_tree
        )
    else:
        result = _read_golden_tree(
            generated_repo_path=generated_repo_path, golden_tree=golden_tree
        )
        if result.returncode != 0:
            print("Generated repo differs from golden repo:")
            print()
            print("STDOUT:")
            print("-" * 80)
            print(result.stdout.decode("utf-8"))
            print("-" * 80)
            print("STDERR:")
            print("-" * 80)
            print(result.stderr.decode("utf-8"))
            print("-" * 80)
            assert result.returncode == 0


def _filter_generation_output(
    result: subprocess.CompletedProcess[bytes], /
) -> tuple[bytes, bytes]:
    """Filter out some lines from the output.

    This is necessary because the output of cookiecutter is not deterministic, so we
    just remove all non-deterministic lines. These are lines that contain the path to
    the generated repo (a temporary directory).
    """
    stdout = b"\n".join(
        l
        for l in result.stdout.splitlines()
        if not l.startswith((b"WARNING: The replay file's `_template` (",))
    )
    return stdout, result.stderr


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
    repo_config_dep = rf"frequenz-repo-config[\1] @ file://{repo_config_path}"
    repo_config_dep_re = re.compile(r"""frequenz-repo-config\[([^]]+)\][^"]+""")

    with open(repo_path / "pyproject.toml", encoding="utf8") as pyproject_file:
        pyproject_content = pyproject_file.read()

    with open(repo_path / "pyproject.toml", "w", encoding="utf8") as pyproject_file:
        pyproject_file.write(repo_config_dep_re.sub(repo_config_dep, pyproject_content))
