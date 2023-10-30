# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Version information for a repository.

This module provides the
[`RepoVersionInfo`][frequenz.repo.config.version.RepoVersionInfo] class to get information
about the repository version.

It handles many scenarios and queries, like:

* Is the current commit a tag or a branch?
* Is the current tag the latest tag?
* Is the current branch the latest branch?
* Is the current tag the last minor version for the major version?
* What is the next minor version for the current major branch?
* etc.

Repository tag names are expected to follow the [semantic versioning][semver]
specification, but usually with a leading `v` (e.g. `v1.0.0`).
[`to_semver()`][frequenz.repo.config.version.to_semver] can be used to convert a version
string to a semantic version, even if it has a leading `v`.

Repository branch names can be parsed with
[`BranchVersion.parse()`][frequenz.repo.config.version.BranchVersion.parse] and are
expected follow the format:

- `vX.x.x` for major branches, where `X` is the major version number. For example,
  `v1.x.x` is the major branch for the major version 1.

  It represents an in-development major version, from which new minor branches
  including new features are created (including the first minor branch for the major
  version).

- `vX.Y.x` for minor branches, where `X` is the major version number and `Y` is the
  minor version number. For example, `v1.0.x` is the minor branch for the major version
  1 and minor version 0.

  It represents a maintained minor version, from which new patch releases (with bug
  fixes) are created. For example, `v1.1.x` is the minor branch for the major version 1
  and minor version 1.

[semver]: https://semver.org/
"""

from __future__ import annotations

import dataclasses
import logging
import pathlib
import re
from typing import Self, TypeGuard

import semver

_logger = logging.getLogger(__name__)
_major_branch_re: re.Pattern[str] = re.compile(r"^v?(\d+)\.x\.x$")
_minor_branch_re: re.Pattern[str] = re.compile(r"^v?(\d+)\.(\d+)\.x$")


def strip_v(version: str) -> str:
    """Strip the leading 'v' from a version string.

    Args:
        version: The version string.

    Returns:
        The version string without the leading 'v'.
    """
    return version[1:] if version.startswith("v") else version


def to_semver(version: str) -> semver.Version | None:
    """Convert a version string to a semantic version.

    Args:
        version: The version string.

    Returns:
        The semantic version or `None` if the version string is not a valid semantic
            version.
    """
    try:
        return semver.Version.parse(strip_v(version))
    except ValueError:
        logging.debug("Version is not a semantic version: %s", version)
        return None


def _build_tags(tags: list[str]) -> dict[str, semver.Version]:
    """Build the tags dictionary.

    Args:
        tags: The tags of the repository.

    Returns:
        The tags dictionary, where the key is the tag name and the value is the
            parsed tag (semantic) version, sorted by semantic version.
    """

    def tag_not_none(
        tag: tuple[str, semver.Version | None]
    ) -> TypeGuard[tuple[str, semver.Version]]:
        return tag[1] is not None

    return dict(
        sorted(
            filter(
                tag_not_none,
                ((tag, to_semver(tag)) for tag in (tags or [])),
            ),
            key=lambda tag: tag[1],
        )
    )


def _build_branches(branches: list[str]) -> dict[str, BranchVersion]:
    """Build the branches dictionary.

    Args:
        branches: The branches of the repository.

    Returns:
        The branches dictionary, where the key is the branch name and the value is
            the parsed branch name, sorted by branch version.
    """

    def branch_not_none(
        branch: tuple[str, BranchVersion | None]
    ) -> TypeGuard[tuple[str, BranchVersion]]:
        return branch[1] is not None

    return dict(
        sorted(
            filter(
                branch_not_none,
                ((branch, BranchVersion.parse(branch)) for branch in (branches or [])),
            ),
            key=lambda branch: branch[1],
        )
    )


@dataclasses.dataclass(frozen=True, kw_only=True)
class BranchVersion:
    """A branch version.

    Versions can be compared with each other. If `minor` is `None`, it is considered to
    be greater than any other `minor`.
    """

    major: int
    """The major version number."""

    minor: int | None = None
    """The minor version number."""

    name: str
    """The branch name."""

    def __post_init__(self) -> None:
        """Post init."""
        if self.major < 0:
            raise ValueError("major cannot be negative")
        if self.minor is not None and self.minor < 0:
            raise ValueError("minor cannot be negative")

    @classmethod
    def parse(cls, branch: str) -> Self | None:
        """Parse a branch name.

        See the [module documentation][frequenz.repo.config.version] for the expected
        format of the branch name.

        Args:
            branch: The branch name.

        Returns:
            The parsed branch version information or None if the branch name is not
                a valid branch name.
        """
        if match := _major_branch_re.match(branch):
            return cls(major=int(match.group(1)), name=branch)
        if match := _minor_branch_re.match(branch):
            return cls(
                major=int(match.group(1)), minor=int(match.group(2)), name=branch
            )
        _logger.debug("Invalid branch name: %s", branch)
        return None

    def __str__(self) -> str:
        """Return the branch name."""
        return self.name

    def __lt__(self, other: BranchVersion) -> bool:
        """Compare two branch version information.

        If `minor` is `None`, it is considered to be greater than any other `minor`.

        Args:
            other: The other branch version information.

        Returns:
            Whether the current branch version information is less than the other.
        """
        if not isinstance(other, BranchVersion):
            return NotImplemented
        if self.minor is None and other.minor is None:
            self_minor = 0
            other_minor = 0
        elif self.minor is None and other.minor is not None:
            self_minor = other.minor + 1
            other_minor = other.minor
        elif other.minor is None and self.minor is not None:
            self_minor = self.minor
            other_minor = self.minor + 1
        elif self.minor is not None and other.minor is not None:
            self_minor = self.minor
            other_minor = other.minor
        else:
            # We need this because mypy is not smart enough to figure it out
            assert False, "unreachable"
        return (self.major, self_minor, self.name) < (
            other.major,
            other_minor,
            other.name,
        )


class RepoVersionInfo:  # pylint: disable=too-many-instance-attributes
    """The information about a repository version.

    The information includes if it is a tag, a branch, if tags and branches are well
    formed, the next minor version, etc.

    This assumes tags follow semantic versioning and branches are in the form
    "v<major>.x.x" or "v<major>.<minor>.x", where <major> and <minor> are integers and
    represent the major and minor for the version being developed in that branch.

    New minor releases are branched from a major branch, also creating a minor branch
    for patch releases for that minor. For example, if the current major version is 1,
    the current major branch is "v1.x.x" and the current minor branch is "v1.0.x". If
    the next minor version is 1.1, the new minor branch will be "v1.1.x".
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        sha: str,
        ref: str,
        tags: list[str] | None = None,
        branches: list[str] | None = None,
    ) -> None:
        """Initialize the environment variables.

        Args:
            sha: The current commit hash.
            ref: The current reference full path (e.g. `refs/tags/v1.0.0`).
            tags: The tags of the repository.
            branches: The branches of the repository.
        """
        self._sha: str = sha
        _logger.debug("sha: %s", self._sha)

        self._ref: str = ref
        _logger.debug("ref: %s", self._ref)

        self._ref_name: str = pathlib.Path(ref).name
        _logger.debug("ref_name: %s", self._ref_name)

        self._current_branch: BranchVersion | None = BranchVersion.parse(self._ref_name)
        _logger.debug("current_branch: %s", self._current_branch)

        self._current_tag: semver.Version | None = to_semver(self._ref_name)
        _logger.debug("current_tag: %s", self._current_tag)

        self._tags: dict[str, semver.Version] = _build_tags(tags or [])
        _logger.debug("tags: %s", self._tags)

        self._branches: dict[str, BranchVersion] = _build_branches(branches or [])
        _logger.debug("branches: %s", self._branches)

    @property
    def sha(self) -> str:
        """The current commit hash."""
        return self._sha

    @property
    def ref(self) -> str:
        """The current reference full path (e.g. `refs/tags/v1.0.0`)."""
        return self._ref

    @property
    def ref_name(self) -> str:
        """The current reference name (e.g. `v1.0.0`)."""
        return self._ref_name

    @property
    def current_branch(self) -> BranchVersion | None:
        """The branch pointing to the current commit.

        `None` if there is no current branch or the name is invalid.
        """
        return self._current_branch

    @property
    def current_tag(self) -> semver.Version | None:
        """The tag pointing to the current commit.

        `None` if there is no tag or the name is invalid.
        """
        return self._current_tag

    @property
    def tags(self) -> dict[str, semver.Version]:
        """The tags of the repository.

        The key is the tag name and the value is the parsed tag (semantic) version.
        """
        return self._tags

    @property
    def branches(self) -> dict[str, BranchVersion]:
        """The branches of the repository.

        The key is the branch name and the value is the parsed branch name.
        """
        return self._branches

    def find_last_tag(self) -> semver.Version | None:
        """Find the last tag.

        Returns:
            If we are at a tag, return the [current
                tag][frequenz.repo.config.version.RepoVersionInfo.current_tag]. If we
                are at a branch, return the last tag matching the branch major and minor
                (if any). If there are no matching tags, return `None`.
        """
        if self._current_tag:
            return self._current_tag
        branch = self.current_branch
        if branch is None:
            return None
        tags = [t for t in self._tags.values() if t.major == branch.major]
        if branch.minor is not None:
            tags = [t for t in tags if t.minor == branch.minor]
        if not tags:
            return None
        return max(tags)

    def find_next_breaking_branch(self) -> BranchVersion | None:
        """Find the next branch potentially introducing breaking changes.

        Returns:
            If there is a last tag, use that as a base, otherwise use the current branch
                as a base. If none is available, return `None`. If there is a base, the
                major is incremented by one and the minor is set to `None`, unless the
                major is 0 (an "initial development version" for semver), in which case
                the major is set to 0 and the minor is incremented by one, as the next
                minor could be a breaking change. Technically semver allows breaking
                changes in patches for major version 0, but we assume patches maintain
                backwards compatibility.
        """
        v_prefix = "v" if self._ref_name.startswith("v") else ""
        last_tag = self.find_last_tag()
        if last_tag is None:
            branch = self.current_branch
            if branch is None:
                _logger.warning(
                    "Trying to get the next breaking branch but there is no (valid) "
                    "last tag nor current branch for %r",
                    self._ref,
                )
                return None
            major = branch.major + 1
            minor = branch.minor or 1
        else:
            major = last_tag.major + 1
            minor = last_tag.minor + 1

        # If the next major is 1, then the current is 0, so the next minor could be
        # a breaking change.
        if major == 1:
            return BranchVersion(major=0, minor=minor, name=f"{v_prefix}0.{minor}.x")

        return BranchVersion(major=major, name=f"{v_prefix}{major}.x.x")

    def find_next_minor_for_major_branch(self) -> int | None:
        """Find the next minor version for the current major branch.

        Returns:
            The next minor version or `None` if there is no current branch, the
                current branch is invalid or is not a major branch.
        """
        branch = self.current_branch
        if branch is None:
            _logger.warning(
                "Trying to get the next minor for the current branch but "
                "the current branch is invalid: %r",
                branch,
            )
            return None

        if branch.minor is not None:
            _logger.warning(
                "Trying to get the next minor for the current branch but "
                "the current branch is not a major branch: %r",
                branch,
            )
            return None

        minor_tags = [
            tag
            for tag in self._tags.values()
            if tag.major == branch.major and tag.prerelease is None
        ]
        if not minor_tags:
            return 0

        bigger_tag = max(minor_tags, key=lambda tag: tag.minor)
        return bigger_tag.minor + 1

    def is_tag(self) -> bool:
        """Tell whether we are at a stable release."""
        return self._ref.startswith("refs/tags/")

    def is_branch(self) -> bool:
        """Tell whether we are at a major branch."""
        return self._ref.startswith("refs/heads/")

    def is_tag_last_minor_for_major(self) -> bool:
        """Tell whether the current tag is the last minor version for the major version.

        If we are not at a tag or there are not tags in the repo, return `False`.

        If the `current_tag` is a pre-release, only pre-release tags are considered and
        if is not a pre-release, only stable tags are considered.
        """
        tag = self.current_tag
        if tag is None:
            _logger.warning(
                "Can't determine if %r is the last minor tag for the major version "
                "because we are not at a tag or the tag is invalid",
                self._ref_name,
            )
            return False
        minor_tags = [tag_ for tag_ in self._tags.values() if tag_.major == tag.major]
        if tag.prerelease is None:
            minor_tags = [tag_ for tag_ in minor_tags if tag_.prerelease is None]
        else:
            minor_tags = [tag_ for tag_ in minor_tags if tag_.prerelease is not None]
        if not minor_tags:
            _logger.debug(
                "No minor tags found for major version %s, considering the "
                "tag %r the last minor for this major",
                tag.major,
                tag,
            )
            return True
        return tag >= max(minor_tags, key=lambda tag_: tag_.minor)

    def is_tag_latest(self) -> bool:
        """Tell whether the current tag is the latest tag.

        The latest tag is the tag with the biggest major, minor and patch
        version. If the current tag is a prerelease, then only prereleases are used to
        determine the biggest.

        Sorting is always according to semver.
        """
        tag = self.current_tag
        if tag is None:
            _logger.warning(
                "Can't determine if %r is the latest tag because we are not at a tag "
                "or the tag is invalid",
                self._ref_name,
            )
            return False
        if tag.prerelease is None:
            tags_it = (tag_ for tag_ in self._tags.values() if tag_.prerelease is None)
        else:
            tags_it = (
                tag_ for tag_ in self._tags.values() if tag_.prerelease is not None
            )
        latest = sorted(tags_it, reverse=True)
        if not latest:
            _logger.warning(
                "No other tags found, at least the current tag %r should be in the list "
                "of tags (%r)",
                tag,
                self._tags,
            )
            return False
        return tag == latest[0]

    def is_branch_latest(self) -> bool:
        """Tell whether the current branch is the latest.

        The latest branch is the branch with the biggest major and minor, but if minor
        is `None`, then it is considered the biggest minor.
        """
        branch = self.current_branch
        if branch is None:
            _logger.warning(
                "Can't determine if %r is the latest branch because we are not at "
                "a branch or the branch is invalid",
                self._ref_name,
            )
            return False
        latest = sorted(self._branches.values(), reverse=True)
        if not latest:
            _logger.warning(
                "No other branches found, at least the current branch %r should be in the list "
                "of branches (%r)",
                branch,
                self._branches,
            )
            return False
        return branch == latest[0]
