# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the version module."""

import dataclasses

import pytest
import semver

from frequenz.repo.config.version import (
    BranchVersion,
    RepoVersionInfo,
    _build_branches,
    _build_tags,
    to_semver,
)


@pytest.mark.parametrize(
    ["version", "expected"],
    [
        ("v1.0.0", semver.Version(1, 0, 0)),
        ("v1.0.0-alpha.1", semver.Version(1, 0, 0, "alpha.1")),
        ("v1.0.0+build.1", semver.Version(1, 0, 0, build="build.1")),
        ("v1.0.0-alpha+build.1", semver.Version(1, 0, 0, "alpha", "build.1")),
        ("v1.0.x", None),
        ("1.0.0", semver.Version(1, 0, 0)),
        ("1.0.0-alpha.1", semver.Version(1, 0, 0, "alpha.1")),
        ("1.0.0+build.1", semver.Version(1, 0, 0, build="build.1")),
        ("1.0.0-alpha+build.1", semver.Version(1, 0, 0, "alpha", "build.1")),
        ("1.0.x", None),
        ("blah", None),
    ],
)
def test_to_semver(version: str, expected: semver.Version | None) -> None:
    """Test to_semver()."""
    actual = to_semver(version)
    if expected is None:
        assert actual is None
    else:
        assert actual is not None
        assert actual == expected


@pytest.mark.parametrize("with_v", [True, False])
@pytest.mark.parametrize(
    ["branch", "expected"],
    [
        ("0.x.x", BranchVersion(major=0, minor=None, name="0.x.x")),
        ("0.0.x", BranchVersion(major=0, minor=0, name="0.0.x")),
        ("1.x.x", BranchVersion(major=1, minor=None, name="1.x.x")),
        ("1.0.x", BranchVersion(major=1, minor=0, name="1.0.x")),
        ("1.1.x", BranchVersion(major=1, minor=1, name="1.1.x")),
        ("", None),
        ("0", None),
        ("1", None),
        ("1.1", None),
        ("-1.x.x", None),
        ("1.-1.x", None),
        ("-0.x.x", None),
        ("1.-0.x", None),
        ("-0.-0.x", None),
        ("1.0.0", None),
        ("1.0.0-alpha+build.1", None),
    ],
)
def test_branch_version_parse(
    branch: str, expected: BranchVersion | None, with_v: bool
) -> None:
    """Test BranchVersion.parse()."""
    if with_v:
        branch = f"v{branch}"
    actual = BranchVersion.parse(branch)
    if with_v and expected is not None and len(expected.name) > 0:
        expected = dataclasses.replace(expected, name=f"v{expected.name}")
    if expected is None:
        assert actual is None
    else:
        assert actual is not None
        assert actual == expected


@pytest.mark.parametrize(
    ["branch_1", "branch_2"],
    [
        ("v1.x.x", "v2.x.x"),
        ("v1.1.x", "v2.x.x"),
        ("v1.1.x", "v2.0.x"),
        ("v1.1.x", "v2.0.x"),
        ("v1.x.x", "v2.0.x"),
        pytest.param("v1.x.x", "v1.x.x", marks=pytest.mark.xfail),
    ],
)
def test_branch_version_comparison(branch_1: str, branch_2: str) -> None:
    """Test BranchVersionInfo.__lt__()."""
    br1 = BranchVersion.parse(branch_1)
    br2 = BranchVersion.parse(branch_2)
    assert br1 is not None
    assert br2 is not None
    assert br1 < br2


@pytest.mark.parametrize(
    ["tags", "expected"],
    [
        ([], {}),
        (["invalid-tag"], {}),
        (["v1.0.1"], {"v1.0.1": semver.Version(1, 0, 1)}),
        (
            ["v1.0.1", "v0.1.0", "blah", "v0.0.1", "v1.0.0", "v2.0.0", "invalid-tag"],
            {
                "v0.0.1": semver.Version(0, 0, 1),
                "v0.1.0": semver.Version(0, 1, 0),
                "v1.0.0": semver.Version(1, 0, 0),
                "v1.0.1": semver.Version(1, 0, 1),
                "v2.0.0": semver.Version(2, 0, 0),
            },
        ),
    ],
    ids=lambda x: str(list(x.keys())) if isinstance(x, dict) else str(x),
)
def test_build_tags(tags: list[str], expected: dict[str, semver.Version]) -> None:
    """Test _build_tags() skip invalid tags and is sorted."""
    assert _build_tags(tags) == expected


@pytest.mark.parametrize(
    ["branches", "expected"],
    [
        ([], {}),
        (["feature-branch", "vx.x.x"], {}),
        (["v1.x.x"], {"v1.x.x": BranchVersion(major=1, minor=None, name="v1.x.x")}),
        (
            ["v1.x.x", "v0.x.x", "x", "v2.x.x", "v1.0.x", "v0.0.x", "feature-branch"],
            {
                "v0.x.x": BranchVersion(major=0, minor=None, name="v0.x.x"),
                "v1.x.x": BranchVersion(major=1, minor=None, name="v1.x.x"),
                "v2.x.x": BranchVersion(major=2, minor=None, name="v2.x.x"),
                "v0.0.x": BranchVersion(major=0, minor=0, name="v0.0.x"),
                "v1.0.x": BranchVersion(major=1, minor=0, name="v1.0.x"),
            },
        ),
    ],
    ids=lambda x: str(list(x.keys())) if isinstance(x, dict) else str(x),
)
def test_build_branches(
    branches: list[str], expected: dict[str, BranchVersion]
) -> None:
    """Test _build_branches() skip invalid branches and is sorted."""
    assert _build_branches(branches) == expected


_test_tags_1 = [
    "v0.0.1",
    "v0.1.0",
    "v1.0.0",
    "v1.0.1",
    "v1.0.2-alpha.1",
    "v1.1.0-beta",
    "v1.1.0-rc",
    "v2.0.0",
    "v2.0.1-rc1",
    "v2.1.0",
]
_test_branches_1 = ["v1.x.x", "v0.x.x", "v0.0.x", "v2.x.x", "v1.0.x"]


@dataclasses.dataclass(frozen=True, kw_only=True)
class _Expected:  # pylint: disable=too-many-instance-attributes
    ref: str
    ref_name: str
    sha: str = "1234567890abcdef"
    # Tag
    current_tag: semver.Version | None = None
    is_tag: bool = False
    is_tag_last_minor_for_major: bool = False
    is_tag_latest: bool = False
    # Branch
    current_branch: BranchVersion | None = None
    is_branch: bool = False
    is_branch_latest: bool = False
    next_minor_for_major_branch: int | None = None


@dataclasses.dataclass(frozen=True, kw_only=True)
class _TestCase:  # pylint: disable=too-many-instance-attributes
    title: str
    ref: str
    sha: str = "1234567890abcdef"
    tags: list[str] = dataclasses.field(default_factory=_test_tags_1.copy)
    branches: list[str] = dataclasses.field(default_factory=_test_branches_1.copy)
    expected: _Expected


_test_cases = [
    _TestCase(
        title="release-bad-version",
        ref="refs/tags/v1.0.a",
        expected=_Expected(
            ref="refs/tags/v1.0.a",
            ref_name="v1.0.a",
            is_tag=True,
        ),
    ),
    _TestCase(
        title="release-new-patch-version",
        ref="refs/tags/v1.0.1",
        expected=_Expected(
            ref="refs/tags/v1.0.1",
            ref_name="v1.0.1",
            current_tag=semver.Version(1, 0, 1),
            is_tag=True,
            is_tag_last_minor_for_major=True,
        ),
    ),
    _TestCase(
        title="release-new-minor-version",
        ref="refs/tags/v1.1.0",
        expected=_Expected(
            ref="refs/tags/v1.1.0",
            ref_name="v1.1.0",
            current_tag=semver.Version(1, 1, 0),
            is_tag=True,
            is_tag_last_minor_for_major=True,
        ),
    ),
    _TestCase(
        title="release-not-latest-minor-for-major",
        ref="refs/tags/v2.0.1",
        expected=_Expected(
            ref="refs/tags/v2.0.1",
            ref_name="v2.0.1",
            current_tag=semver.Version(2, 0, 1),
            is_tag=True,
            is_tag_last_minor_for_major=False,
        ),
    ),
    _TestCase(
        title="release-latest-major",
        ref="refs/tags/v3.0.0",
        tags=_test_tags_1 + ["v3.0.0"],
        expected=_Expected(
            ref="refs/tags/v3.0.0",
            ref_name="v3.0.0",
            current_tag=semver.Version(3, 0, 0),
            is_tag=True,
            is_tag_last_minor_for_major=True,
            is_tag_latest=True,
        ),
    ),
    _TestCase(
        title="release-latest-minor",
        ref="refs/tags/v2.1.0",
        expected=_Expected(
            ref="refs/tags/v2.1.0",
            ref_name="v2.1.0",
            current_tag=semver.Version(2, 1, 0),
            is_tag=True,
            is_tag_last_minor_for_major=True,
            is_tag_latest=True,
        ),
    ),
    _TestCase(
        title="release-latest-patch",
        ref="refs/tags/v2.1.1",
        tags=_test_tags_1 + ["v2.1.1"],
        expected=_Expected(
            ref="refs/tags/v2.1.1",
            ref_name="v2.1.1",
            current_tag=semver.Version(2, 1, 1),
            is_tag=True,
            is_tag_last_minor_for_major=True,
            is_tag_latest=True,
        ),
    ),
    _TestCase(
        title="pre-release-new-patch-version",
        ref="refs/tags/v1.0.2-alpha.1",
        tags=_test_tags_1,
        expected=_Expected(
            ref="refs/tags/v1.0.2-alpha.1",
            ref_name="v1.0.2-alpha.1",
            current_tag=semver.Version(1, 0, 2, "alpha.1"),
            is_tag=True,
        ),
    ),
    _TestCase(
        title="pre-release-new-minor-version",
        ref="refs/tags/v1.1.0-beta",
        tags=_test_tags_1,
        expected=_Expected(
            ref="refs/tags/v1.1.0-beta",
            ref_name="v1.1.0-beta",
            current_tag=semver.Version(1, 1, 0, "beta"),
            is_tag=True,
            is_tag_last_minor_for_major=True,
        ),
    ),
    _TestCase(
        title="pre-release-latest-major",
        ref="refs/tags/v3.0.0-rc1",
        tags=_test_tags_1 + ["v3.0.0-rc1"],
        expected=_Expected(
            ref="refs/tags/v3.0.0-rc1",
            ref_name="v3.0.0-rc1",
            current_tag=semver.Version(3, 0, 0, "rc1"),
            is_tag=True,
            is_tag_last_minor_for_major=True,
            is_tag_latest=True,
        ),
    ),
    _TestCase(
        title="pre-release-latest-minor",
        ref="refs/tags/v2.1.0-alpha.1",
        tags=_test_tags_1 + ["v2.1.0-alpha.1"],
        expected=_Expected(
            ref="refs/tags/v2.1.0-alpha.1",
            ref_name="v2.1.0-alpha.1",
            current_tag=semver.Version(2, 1, 0, "alpha.1"),
            is_tag=True,
            is_tag_last_minor_for_major=True,
            is_tag_latest=True,
        ),
    ),
    _TestCase(
        title="pre-release-latest-patch",
        ref="refs/tags/v2.0.1-rc1",
        tags=_test_tags_1,
        expected=_Expected(
            ref="refs/tags/v2.0.1-rc1",
            ref_name="v2.0.1-rc1",
            current_tag=semver.Version(2, 0, 1, "rc1"),
            is_tag=True,
            is_tag_last_minor_for_major=True,
            is_tag_latest=True,
        ),
    ),
    _TestCase(
        title="branch-bad",
        ref="refs/heads/vx.x.x",
        expected=_Expected(
            ref="refs/heads/vx.x.x",
            ref_name="vx.x.x",
            current_branch=None,
            is_branch=True,
        ),
    ),
    _TestCase(
        title="branch-major",
        ref="refs/heads/v1.x.x",
        expected=_Expected(
            ref="refs/heads/v1.x.x",
            ref_name="v1.x.x",
            current_branch=BranchVersion(major=1, minor=None, name="v1.x.x"),
            is_branch=True,
            next_minor_for_major_branch=1,
        ),
    ),
    _TestCase(
        title="branch-minor",
        ref="refs/heads/v1.0.x",
        expected=_Expected(
            ref="refs/heads/v1.0.x",
            ref_name="v1.0.x",
            current_branch=BranchVersion(major=1, minor=0, name="v1.0.x"),
            is_branch=True,
        ),
    ),
    _TestCase(
        title="release-new-patch-version-no-tags",
        ref="refs/tags/v1.0.0",
        tags=[],
        expected=_Expected(
            ref="refs/tags/v1.0.0",
            ref_name="v1.0.0",
            current_tag=semver.Version(1, 0, 0),
            is_tag=True,
            is_tag_last_minor_for_major=True,
        ),
    ),
    _TestCase(
        title="release-new-patch-version-no-branches-last-minor",
        ref="refs/tags/v1.0.2",
        branches=[],
        expected=_Expected(
            ref="refs/tags/v1.0.2",
            ref_name="v1.0.2",
            current_tag=semver.Version(1, 0, 2),
            is_tag=True,
            is_tag_last_minor_for_major=True,
        ),
    ),
    _TestCase(
        title="release-new-patch-version-no-branches-not-last-minor",
        ref="refs/tags/v2.0.1",
        branches=[],
        expected=_Expected(
            ref="refs/tags/v2.0.1",
            ref_name="v2.0.1",
            current_tag=semver.Version(2, 0, 1),
            is_tag=True,
        ),
    ),
    _TestCase(
        title="release-new-patch-version-no-tags-no-branches",
        ref="refs/tags/v1.0.0",
        tags=[],
        branches=[],
        expected=_Expected(
            ref="refs/tags/v1.0.0",
            ref_name="v1.0.0",
            current_tag=semver.Version(1, 0, 0),
            is_tag=True,
            is_tag_last_minor_for_major=True,
        ),
    ),
    _TestCase(
        title="branch-major-no-tags",
        ref="refs/heads/v1.x.x",
        tags=[],
        expected=_Expected(
            ref="refs/heads/v1.x.x",
            ref_name="v1.x.x",
            current_branch=BranchVersion(major=1, minor=None, name="v1.x.x"),
            is_branch=True,
            next_minor_for_major_branch=0,
        ),
    ),
    _TestCase(
        title="branch-major-no-branches",
        ref="refs/heads/v1.x.x",
        branches=[],
        expected=_Expected(
            ref="refs/heads/v1.x.x",
            ref_name="v1.x.x",
            current_branch=BranchVersion(major=1, minor=None, name="v1.x.x"),
            is_branch=True,
            next_minor_for_major_branch=1,
        ),
    ),
    _TestCase(
        title="branch-major-no-tags-no-branches",
        ref="refs/heads/v1.x.x",
        tags=[],
        branches=[],
        expected=_Expected(
            ref="refs/heads/v1.x.x",
            ref_name="v1.x.x",
            current_branch=BranchVersion(major=1, minor=None, name="v1.x.x"),
            is_branch=True,
            next_minor_for_major_branch=0,
        ),
    ),
]


@pytest.mark.parametrize("case", _test_cases, ids=lambda x: x.title)
def test_repo_version(
    case: _TestCase,
) -> None:
    """Test RepoVersionInfo."""
    repo_version_info = RepoVersionInfo(
        sha=case.sha,
        ref=case.ref,
        tags=case.tags,
        branches=case.branches,
    )
    assert repo_version_info.sha == case.expected.sha
    assert repo_version_info.ref == case.expected.ref
    assert repo_version_info.ref_name == case.expected.ref_name
    assert repo_version_info.current_branch == case.expected.current_branch
    # semver.Version doesn't support comparing to None
    if case.expected.current_tag is None:
        assert repo_version_info.current_tag is None
    else:
        assert repo_version_info.current_tag is not None
        assert repo_version_info.current_tag == case.expected.current_tag
    assert (
        repo_version_info.find_next_minor_for_major_branch()
        == case.expected.next_minor_for_major_branch
    )
    assert repo_version_info.is_tag() == case.expected.is_tag
    assert repo_version_info.is_branch() == case.expected.is_branch
    assert (
        repo_version_info.is_tag_last_minor_for_major()
        == case.expected.is_tag_last_minor_for_major
    )
    assert repo_version_info.is_tag_latest() == case.expected.is_tag_latest
    assert repo_version_info.is_branch_latest() == case.expected.is_branch_latest
