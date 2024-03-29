# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the mike module."""

import dataclasses
from typing import assert_never
from unittest import mock

import pytest
import semver

from frequenz.repo.config.mkdocs.mike import (
    MikeVersionInfo,
    build_mike_version,
    compare_mike_version,
    sort_mike_versions,
)
from frequenz.repo.config.version import BranchVersion, RepoVersionInfo


@dataclasses.dataclass(frozen=True, kw_only=True)
class _BuildVersionTestCase:  # pylint: disable=too-many-instance-attributes
    title: str
    # Common
    ref_name: str
    sha: str = "1234567890abcdef"
    ref: str = "mock-ref"
    # Tag
    is_tag: bool = False
    is_tag_last_minor_for_major: bool = False
    is_tag_latest: bool = False
    # Branch
    is_branch: bool = False
    is_branch_latest: bool = False
    next_minor_for_major_branch: int | None = None
    expected: MikeVersionInfo | Exception


_build_version_test_cases = [
    _BuildVersionTestCase(
        title="invalid-release",
        ref_name="vx.x.x",
        is_tag=True,
        expected=ValueError("The tag 'vx.x.x' is not a valid semver version"),
    ),
    _BuildVersionTestCase(
        title="pre-release-latest",
        ref_name="v1.2.3-rc.1",
        is_tag=True,
        is_tag_last_minor_for_major=True,
        is_tag_latest=True,
        expected=MikeVersionInfo(
            title="v1.2.3-rc.1",
            version="v1.2-pre",
            aliases=["v1-pre", "latest-pre"],
        ),
    ),
    _BuildVersionTestCase(
        title="pre-release-last-minor-for-major",
        ref_name="v1.2.3-rc.1",
        is_tag=True,
        is_tag_last_minor_for_major=True,
        expected=MikeVersionInfo(
            title="v1.2.3-rc.1",
            version="v1.2-pre",
            aliases=["v1-pre"],
        ),
    ),
    _BuildVersionTestCase(
        title="pre-release-old-minor",
        ref_name="v1.2.3-rc.1",
        is_tag=True,
        expected=MikeVersionInfo(
            title="v1.2.3-rc.1",
            version="v1.2-pre",
            aliases=[],
        ),
    ),
    _BuildVersionTestCase(
        title="release-latest",
        ref_name="v1.2.3",
        is_tag=True,
        is_tag_last_minor_for_major=True,
        is_tag_latest=True,
        expected=MikeVersionInfo(
            title="v1.2.3",
            version="v1.2",
            aliases=["v1", "latest"],
        ),
    ),
    _BuildVersionTestCase(
        title="release-last-minor-for-major-branch",
        ref_name="v1.2.3",
        is_tag=True,
        is_tag_last_minor_for_major=True,
        expected=MikeVersionInfo(
            title="v1.2.3",
            version="v1.2",
            aliases=["v1"],
        ),
    ),
    _BuildVersionTestCase(
        title="release-old-minor",
        ref_name="v1.2.3",
        is_tag=True,
        expected=MikeVersionInfo(
            title="v1.2.3",
            version="v1.2",
            aliases=[],
        ),
    ),
    _BuildVersionTestCase(
        title="released-major-branch",
        ref_name="v1.x.x",
        is_branch=True,
        next_minor_for_major_branch=3,
        expected=MikeVersionInfo(
            title="v1.3-dev (1234567)",
            version="v1.3-dev",
            aliases=["v1-dev"],
        ),
    ),
    _BuildVersionTestCase(
        title="unreleased-major-branch",
        ref_name="v1.x.x",
        is_branch=True,
        next_minor_for_major_branch=0,
        expected=MikeVersionInfo(
            title="v1.0-dev (1234567)",
            version="v1.0-dev",
            aliases=["v1-dev"],
        ),
    ),
    _BuildVersionTestCase(
        title="released-latest-major-branch",
        ref_name="v1.x.x",
        is_branch=True,
        is_branch_latest=True,
        next_minor_for_major_branch=3,
        expected=MikeVersionInfo(
            title="v1.3-dev (1234567)",
            version="v1.3-dev",
            aliases=["v1-dev", "latest-dev"],
        ),
    ),
    _BuildVersionTestCase(
        title="unreleased-latest-major-branch",
        ref_name="v1.x.x",
        is_branch=True,
        is_branch_latest=True,
        next_minor_for_major_branch=0,
        expected=MikeVersionInfo(
            title="v1.0-dev (1234567)",
            version="v1.0-dev",
            aliases=["v1-dev", "latest-dev"],
        ),
    ),
    _BuildVersionTestCase(
        title="minor-branch",
        ref_name="v1.0.x",
        is_branch=True,
        expected=MikeVersionInfo(
            title="v1.0-dev (1234567)",
            version="v1.0-dev",
            aliases=[],
        ),
    ),
    _BuildVersionTestCase(
        title="invalid-ref",  # Not a tag nor a branch
        ref_name="vx.x.x",
        expected=ValueError(
            "Don't know how to handle 'mock-ref' to make 'mike' version"
        ),
    ),
    _BuildVersionTestCase(
        title="invalid-tag",
        ref_name="vx1.0.x",
        is_tag=True,
        expected=ValueError("The tag 'vx1.0.x' is not a valid semver version"),
    ),
    _BuildVersionTestCase(
        title="invalid-branch",
        ref_name="feature-branch",
        is_branch=True,
        expected=ValueError("The branch 'feature-branch' is not a valid branch name"),
    ),
]


@pytest.mark.parametrize("case", _build_version_test_cases, ids=lambda c: c.title)
def test_build_mike_version(
    case: _BuildVersionTestCase,
) -> None:
    """Test build_mike_version()."""
    repo_info = mock.MagicMock(spec=RepoVersionInfo)

    # Common
    repo_info.ref_name = case.ref_name
    repo_info.sha = case.sha
    repo_info.ref = case.ref

    # Tag
    try:
        repo_info.current_tag = semver.VersionInfo.parse(case.ref_name[1:])
    except ValueError:
        repo_info.current_tag = None
    repo_info.is_tag.return_value = case.is_tag
    repo_info.is_tag_last_minor_for_major.return_value = (
        case.is_tag_last_minor_for_major
    )
    repo_info.is_tag_latest.return_value = case.is_tag_latest

    # Branch
    try:
        repo_info.current_branch = BranchVersion.parse(case.ref_name)
    except ValueError:
        repo_info.current_branch = case.ref_name
    repo_info.is_branch.return_value = case.is_branch
    repo_info.is_branch_latest.return_value = case.is_branch_latest
    repo_info.find_next_minor_for_major_branch.return_value = (
        case.next_minor_for_major_branch
    )

    # Test
    match case.expected:
        case Exception() as expected_exception:
            with pytest.raises(type(expected_exception), match=str(expected_exception)):
                build_mike_version(repo_info)
        case MikeVersionInfo() as expected_mike_version:
            mike_version = build_mike_version(repo_info)
            assert mike_version == expected_mike_version
        case _ as unhandled:
            assert_never(unhandled)


@pytest.mark.parametrize(
    "version1, version2, expected",
    [
        ("v1.0", "v1.0", 0),
        ("v1.0-dev", "v1.0-dev", 0),
        ("v1.0-pre", "v1.0-pre", 0),
        ("v1.0", "v1.0-dev", -1),
        ("v1.0", "v1.0-pre", 1),
        ("v1.0-dev", "v1.0-pre", 1),
        ("v1.0-dev", "v1.0", 1),
        ("v1.0-pre", "v1.0", -1),
        ("v1.0-pre", "v1.0-dev", -1),
        ("v1.0", "v1.1", -1),
        ("v1.0", "v1.1-dev", -1),
        ("v1.0", "v1.1-pre", -1),
        ("v1.0-dev", "v1.1", -1),
        ("v1.0-dev", "v1.1-dev", -1),
        ("v1.0-dev", "v1.1-pre", -1),
        ("v1.0-pre", "v1.1", -1),
        ("v1.0-pre", "v1.1-dev", -1),
        ("v1.0-pre", "v1.1-pre", -1),
        ("v1.1", "v1.0", 1),
        ("v1.1", "v1.0-dev", 1),
        ("v1.1", "v1.0-pre", 1),
        ("v1.1-dev", "v1.0", 1),
        ("v2.0-dev", "v1.0-dev", 1),
        ("v2.0-pre", "v1.0-dev", 1),
        ("v2.0", "v1.0-dev", 1),
        ("v2.0-dev", "v1.0-pre", 1),
        ("v2.0-pre", "v1.0-pre", 1),
        ("v2.0", "v1.0-pre", 1),
        ("blah", "v1.0-dev", 1),
        ("alpha", "beta", -1),
    ],
)
def test_compare_mike_version(
    version1: str,
    version2: str,
    expected: int,
) -> None:
    """Test compare_mike_version()."""
    assert compare_mike_version(version1, version2) == expected


@dataclasses.dataclass(frozen=True, kw_only=True)
class _SortVersionsTestCase:
    title: str
    versions: list[str]
    reversed: bool = True
    expected: list[str]


_sort_versions_test_cases = [
    _SortVersionsTestCase(
        title="case1",
        versions=["v1.0", "v1.0-dev", "v1.0-pre"],
        expected=["v1.0-dev", "v1.0", "v1.0-pre"],
    ),
    _SortVersionsTestCase(
        title="case2",
        versions=["v1.0", "v2.0", "v3.0", "v3.1"],
        expected=["v3.1", "v3.0", "v2.0", "v1.0"],
    ),
    _SortVersionsTestCase(
        title="case3",
        versions=["v1.0", "v1.0-dev", "v1.0-pre", "v1.1", "v1.1-dev"],
        expected=["v1.1-dev", "v1.1", "v1.0-dev", "v1.0", "v1.0-pre"],
    ),
    _SortVersionsTestCase(
        title="case4",
        versions=["v1.0", "v1.0-dev", "v1.0-pre", "v1.1", "v1.1-dev", "v1.1-pre"],
        expected=["v1.1-dev", "v1.1", "v1.1-pre", "v1.0-dev", "v1.0", "v1.0-pre"],
    ),
    _SortVersionsTestCase(
        title="case5",
        versions=[
            "v1.0",
            "v1.0-dev",
            "v1.0-pre",
            "v0.99-pre",
            "v0.1",
            "v0.99",
            "v0.99-dev",
            "v1.1",
            "alpha",
            "v1.1-dev",
            "v1.1-pre",
            "v2.0",
            "blah",
        ],
        expected=[
            "blah",
            "alpha",
            "v2.0",
            "v1.1-dev",
            "v1.1",
            "v1.1-pre",
            "v1.0-dev",
            "v1.0",
            "v1.0-pre",
            "v0.99-dev",
            "v0.99",
            "v0.99-pre",
            "v0.1",
        ],
    ),
    _SortVersionsTestCase(
        title="case5-not-reversed",
        versions=[
            "v1.0",
            "v1.0-dev",
            "v1.0-pre",
            "v0.99-pre",
            "v0.1",
            "v0.99",
            "v0.99-dev",
            "v1.1",
            "alpha",
            "v1.1-dev",
            "v1.1-pre",
            "v2.0",
            "blah",
        ],
        reversed=False,
        expected=[
            "v0.1",
            "v0.99-pre",
            "v0.99",
            "v0.99-dev",
            "v1.0-pre",
            "v1.0",
            "v1.0-dev",
            "v1.1-pre",
            "v1.1",
            "v1.1-dev",
            "v2.0",
            "alpha",
            "blah",
        ],
    ),
]


@pytest.mark.parametrize("case", _sort_versions_test_cases, ids=lambda c: c.title)
def test_sort_mike_versions(
    case: _SortVersionsTestCase,
) -> None:
    """Test sort_mike_versions()."""
    assert sort_mike_versions(case.versions, reverse=case.reversed) == case.expected
