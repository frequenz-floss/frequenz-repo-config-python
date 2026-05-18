"""Tests for the dependabot-gprc-fixer script."""

import json
import re
import runpy
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

FIXER_PATH = (
    Path(__file__).resolve().parents[3]
    / "cookiecutter/scripts/dependabot-grpc-fixer.py"
)

PYPROJECT = Path("pyproject.toml")

CASE_ROOT = Path(__file__).with_name("fixtures") / "dependabot-grpc-fixer"


@dataclass(frozen=True)
class Case:
    """A single file-based test case."""

    path: Path
    stdout_exact: str | None
    stdout_contains: str | None
    stderr_exact: str | None
    stderr_contains: str | None

    @property
    def expected_pyproject(self) -> Path:
        """Return the expected `pyproject.toml` path for the case."""
        return self.path / "expected" / "pyproject.toml"


def _case_dirs() -> list[Path]:
    """Return all fixture case directories."""
    case_dirs = sorted(path for path in CASE_ROOT.iterdir() if path.is_dir())
    if not case_dirs:
        raise AssertionError(f"no fixture cases found in {CASE_ROOT}")
    return case_dirs


def _read_optional(path: Path) -> str | None:
    """Read a file if it exists."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def _read_contains(path: Path) -> str | None:
    """Read a partial-match expectation if it exists."""
    if path.exists():
        return path.read_text(encoding="utf-8").rstrip("\n")
    return None


def _load_case(case_dir: Path) -> Case:
    """Load a case and its optional output expectations."""
    expected_dir = case_dir / "expected"
    return Case(
        path=case_dir,
        stdout_exact=_read_optional(expected_dir / "stdout.txt"),
        stdout_contains=_read_contains(expected_dir / "stdout.contains.txt"),
        stderr_exact=_read_optional(expected_dir / "stderr.txt"),
        stderr_contains=_read_contains(expected_dir / "stderr.contains.txt"),
    )


def _prepare_workspace(
    case: Case,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Copy fixture inputs into a temp workspace and set env vars."""
    input_dir = case.path / "input"
    input_pyproject = input_dir / "pyproject.toml"
    if input_pyproject.exists():
        shutil.copyfile(input_pyproject, tmp_path / PYPROJECT.name)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [str(FIXER_PATH)])
    input_metadata = input_dir / "dependabot-metadata.json"
    monkeypatch.setenv(
        "UPDATED_DEPENDENCIES_JSON",
        input_metadata.read_text(encoding="utf-8") if input_metadata.exists() else "",
    )
    return tmp_path / PYPROJECT.name


@pytest.mark.parametrize(
    "case", map(_load_case, _case_dirs()), ids=lambda case: case.path.name
)
def test_fixer_cases(
    case: Case,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Apply each case and compare the rewritten files and output."""
    workspace = _prepare_workspace(case, tmp_path, monkeypatch)
    if case.stderr_exact is not None or case.stderr_contains is not None:
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(str(FIXER_PATH), run_name="__main__")
        assert excinfo.value.code == 1
    else:
        runpy.run_path(str(FIXER_PATH), run_name="__main__")

    captured = capsys.readouterr()

    if case.stdout_exact is not None:
        assert captured.out == case.stdout_exact
    elif case.stdout_contains is not None:
        assert case.stdout_contains in captured.out
    else:
        assert captured.out == ""

    if case.stderr_exact is not None:
        assert captured.err == case.stderr_exact
    elif case.stderr_contains is not None:
        assert case.stderr_contains in captured.err
    else:
        assert captured.err == ""

    expected_pyproject = case.expected_pyproject
    if expected_pyproject.exists():
        assert workspace.read_text(encoding="utf-8") == expected_pyproject.read_text(
            encoding="utf-8"
        )


def test_fixer_runs_as_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exercise the module's `__main__` entrypoint."""
    case = _load_case(CASE_ROOT / "update_runtime_bounds")
    workspace = _prepare_workspace(case, tmp_path, monkeypatch)

    monkeypatch.setattr(sys, "argv", [str(FIXER_PATH)])

    runpy.run_path(str(FIXER_PATH), run_name="__main__")

    captured = capsys.readouterr()
    assert (
        captured.out == "Updated pyproject.toml with 2 grpc/protobuf constraint(s).\n"
    )
    assert captured.err == ""
    assert workspace.read_text(encoding="utf-8") == case.expected_pyproject.read_text(
        encoding="utf-8"
    )


def test_fixer_runs_as_script_with_custom_pyproject_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exercise the module's `__main__` entrypoint with a custom path."""
    case = _load_case(CASE_ROOT / "update_runtime_bounds")
    workspace = _prepare_workspace(case, tmp_path, monkeypatch)
    input_pyproject = case.path / "input" / "pyproject.toml"
    custom_pyproject = tmp_path / "custom" / "pyproject.toml"
    custom_pyproject.parent.mkdir(parents=True)
    shutil.copyfile(input_pyproject, custom_pyproject)

    monkeypatch.setattr(
        sys,
        "argv",
        [str(FIXER_PATH), str(custom_pyproject.relative_to(tmp_path))],
    )

    runpy.run_path(str(FIXER_PATH), run_name="__main__")

    captured = capsys.readouterr()
    assert (
        captured.out
        == "Updated custom/pyproject.toml with 2 grpc/protobuf constraint(s).\n"
    )
    assert captured.err == ""
    assert workspace.read_text(encoding="utf-8") == input_pyproject.read_text(
        encoding="utf-8"
    )
    assert custom_pyproject.read_text(
        encoding="utf-8"
    ) == case.expected_pyproject.read_text(encoding="utf-8")


# Integration: run the fixer against pyproject.toml files generated by the
# cookiecutter template (as captured in tests_golden/). The fixer only applies
# to API repositories, so we discover every `api*` golden case automatically.
# This catches drift between the template's runtime range formatting and the
# regexes in cookiecutter/scripts/dependabot-grpc-fixer.py.
GOLDEN_API_PYPROJECTS = sorted(
    (Path(__file__).resolve().parents[3] / "tests_golden").glob(
        "integration/test_cookiecutter_generation/api*/*/pyproject.toml"
    )
)

# Upper-bound offsets the fixer applies per runtime dependency (mirrors
# `UPPER_BOUND_OFFSETS` in dependabot-grpc-fixer.py). Kept here independently so
# the test fails loudly if the offsets diverge from the documented contract.
EXPECTED_UPPER_BOUND_OFFSETS = {"protobuf": 2, "grpcio": 1}


def _golden_id(path: Path) -> str:
    """Return a short pytest id derived from the golden case directory."""
    # .../test_cookiecutter_generation/<case>/<repo>/pyproject.toml
    return path.parent.parent.name


def _extract_runtime_bound(text: str, name: str) -> tuple[str, int]:
    """Return ``(floor, upper_major)`` for ``name`` from a pyproject text.

    Uses the same shape the fixer's regex expects so that a template format
    change makes this helper raise with a clear message before the test
    fabricates a bogus dependabot payload.
    """
    pattern = rf'"{re.escape(name)}\s*>=\s*([^,"]+)\s*,\s*<\s*([^"]+)"'
    matches = re.findall(pattern, text)
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one {name} runtime range in the golden "
            f"pyproject.toml; found {len(matches)}: {matches!r}. The api "
            "template format may have drifted from the fixer's contract."
        )
    floor, upper = matches[0]
    return floor.strip(), int(upper.strip())


def _bump_major(version: str) -> str:
    """Return ``version`` with its major component incremented by one."""
    match = re.match(r"v?(\d+)(.*)", version.strip())
    if match is None:
        raise AssertionError(f"could not parse version {version!r}")
    return f"{int(match.group(1)) + 1}{match.group(2)}"


def _major_number(version: str) -> int:
    """Return the major number from a version string."""
    match = re.match(r"\d+", version)
    if match is None:
        raise AssertionError(f"could not parse major number from {version!r}")
    return int(match.group(0))


def _make_dependabot_metadata(*, protobuf_version: str, grpcio_version: str) -> str:
    """Build a realistic dependabot ``UPDATED_DEPENDENCIES_JSON`` payload."""
    return json.dumps(
        [
            {
                "dependencyName": "grpcio",
                "dependencyType": "direct:production",
                "updateType": "version-update:semver-major",
                "directory": "/",
                "packageEcosystem": "pip",
                "newVersion": grpcio_version,
            },
            {
                "dependencyName": "grpcio-tools",
                "dependencyType": "direct:development",
                "updateType": "version-update:semver-major",
                "directory": "/",
                "packageEcosystem": "pip",
                "newVersion": grpcio_version,
            },
            {
                "dependencyName": "protobuf",
                "dependencyType": "direct:production",
                "updateType": "version-update:semver-major",
                "directory": "/",
                "packageEcosystem": "pip",
                "newVersion": protobuf_version,
            },
        ]
    )


@pytest.mark.parametrize("golden_pyproject", GOLDEN_API_PYPROJECTS, ids=_golden_id)
def test_fixer_against_generated_api_pyproject(
    golden_pyproject: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Apply the fixer to a freshly generated API repo's ``pyproject.toml``.

    This guards against template drift: if the API template stops emitting the
    exact ``"<dep> >= X, < Y", # Do not widen beyond Y!`` shape that the fixer
    relies on, the regex-based replacement will fail to find a match and this
    test will surface the breakage.

    The "new" versions injected via dependabot metadata are derived from the
    golden file's current bounds (next major) so the test always exercises a
    real bump even after the template's pinned versions get bumped.
    """
    assert GOLDEN_API_PYPROJECTS, (
        "no api golden pyproject.toml fixtures discovered; refresh the golden "
        "tree with `UPDATE_GOLDEN=1 pytest tests/integration/"
        "test_cookiecutter_generation.py::test_golden`"
    )

    original = golden_pyproject.read_text(encoding="utf-8")

    # Derive realistic "new" versions from the golden's current bounds. Bumping
    # the major guarantees the fixer rewrites both the floor and the upper
    # bound, even if the template later raises its pinned versions.
    protobuf_floor, protobuf_upper = _extract_runtime_bound(original, "protobuf")
    grpcio_floor, grpcio_upper = _extract_runtime_bound(original, "grpcio")
    new_protobuf = _bump_major(protobuf_floor)
    new_grpcio = _bump_major(grpcio_floor)
    expected_protobuf_upper = (
        _major_number(new_protobuf) + EXPECTED_UPPER_BOUND_OFFSETS["protobuf"]
    )
    expected_grpcio_upper = (
        _major_number(new_grpcio) + EXPECTED_UPPER_BOUND_OFFSETS["grpcio"]
    )
    # Sanity: the derived "new" bounds must actually differ from the originals,
    # otherwise the test would silently no-op.
    assert new_protobuf != protobuf_floor
    assert new_grpcio != grpcio_floor
    assert expected_protobuf_upper != protobuf_upper
    assert expected_grpcio_upper != grpcio_upper

    workspace = tmp_path / PYPROJECT.name
    shutil.copyfile(golden_pyproject, workspace)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [str(FIXER_PATH)])
    monkeypatch.setenv(
        "UPDATED_DEPENDENCIES_JSON",
        _make_dependabot_metadata(
            protobuf_version=new_protobuf, grpcio_version=new_grpcio
        ),
    )

    runpy.run_path(str(FIXER_PATH), run_name="__main__")

    captured = capsys.readouterr()
    assert (
        captured.out == "Updated pyproject.toml with 2 grpc/protobuf constraint(s).\n"
    )
    assert captured.err == ""

    updated = workspace.read_text(encoding="utf-8")
    expected_protobuf_line = (
        f'"protobuf >= {new_protobuf}, < {expected_protobuf_upper}", '
        f"# Do not widen beyond {expected_protobuf_upper}!"
    )
    expected_grpcio_line = (
        f'"grpcio >= {new_grpcio}, < {expected_grpcio_upper}", '
        f"# Do not widen beyond {expected_grpcio_upper}!"
    )
    assert expected_protobuf_line in updated
    assert expected_grpcio_line in updated
    # The original bounds must be gone (proves the rewrite actually happened).
    assert f'"protobuf >= {protobuf_floor}, < {protobuf_upper}"' not in updated
    assert f'"grpcio >= {grpcio_floor}, < {grpcio_upper}"' not in updated
