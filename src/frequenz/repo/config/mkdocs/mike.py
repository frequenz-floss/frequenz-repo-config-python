# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tools to work with mike.

This module provides these tools:

* Building the mike version information from the repository information
  ([`build_mike_version()`][frequenz.repo.config.mkdocs.mike.build_mike_version]).
* Sorting the mike version information `version.json` file
  ([`sort_mike_versions()`][frequenz.repo.config.mkdocs.mike.sort_mike_versions]).
* Comparing mike versions
  ([`compare_mike_version()`][frequenz.repo.config.mkdocs.mike.compare_mike_version]).

Mike versions have the format `vX.Y(-pre|-dev)?`, where `X` is the major version, `Y` is
the minor version, and the optional suffix is either `-pre` for pre-release versions or
`-dev` for development versions.

Stable (tagged) versions have the format `vX.Y`, unless they are pre-release versions,
then they have the format `vX.Y-pre`. Develoment branches have the format `vX.Y-dev`.

* Tag `v1.0.0` -> `v1.0`
* Tag `v2.1.0-alpha.1` -> `v2.1-pre`
* Branch `v1.x.x` (with no releases) -> `v1.0-dev`
* Branch `v1.x.x (with releases an existing release, for example `v1.0.0`) -> `v1.1-dev`
* Branch `v1.1.x` -> `v1.1-dev`

Aliases have the format `vX(-pre|-dev)?`, where `X` is the major version and the
optional suffix is either `-pre` for pre-release versions or `-dev` for development
versions. An alias is also provided to point to the latest version, which is `latest`
for stable versions, `latest-pre` for pre-release versions, and `latest-dev` for
development versions.
"""

import dataclasses
import functools
import re

import semver

from ..version import RepoVersionInfo


@dataclasses.dataclass(frozen=True, kw_only=True)
class MikeVersionInfo:
    """The information needed to publish a mike version.

    This is what mike needs when publishing documentation for a particular version.
    """

    version: str
    """The version identifier of this version."""

    title: str = ""
    """The title of this version."""

    aliases: list[str] = dataclasses.field(default_factory=list)
    """The aliases of this version."""


def build_mike_version(repo_info: RepoVersionInfo) -> MikeVersionInfo:
    """Build the mike version information from the given repository information.

    The version is build based on if a tag or a branch is checked out.

    For tags, the title is the tag name, the version is "vX.Y", where X is the major
    version and Y is the minor version of the tag. If the tag is the last minor version
    for the major version, the alias "vX" is added. If the tag is the latest tag, the
    alias "latest" is added.

    For pre-release tags it's the same but the "-pre" suffix is added to the version and
    the aliases.

    For branches, the title is "vX.Y-dev (SHA)", where X is the major version and Y is
    the minor version of the branch. The version is "vX.Y-dev". If the branch is the
    latest branch, the alias "latest-dev" is added.

    Args:
        repo_info: The repository information.

    Returns:
        The mike version.

    Raises:
        ValueError: If the given repository information is invalid or versions can't be
            determined for some other reason.
    """
    title: str = ""
    version: str = ""
    aliases: list[str] = []

    if repo_info.is_tag():
        current_tag = repo_info.current_tag
        if current_tag is None:
            raise ValueError(
                f"The tag {repo_info.ref_name!r} is not a valid semver version",
            )
        suffix = ""
        if current_tag.prerelease is not None:
            suffix = "-pre"
        title = repo_info.ref_name  # vX.Y.Z
        version = f"v{current_tag.major}.{current_tag.minor}{suffix}"  # vX.Y(-pre)?
        if repo_info.is_tag_last_minor_for_major():
            aliases.append(f"v{current_tag.major}{suffix}")  # vX(-pre)?
        if repo_info.is_tag_latest():
            aliases.append(f"latest{suffix}")  # latest(-pre)?
        return MikeVersionInfo(title=title, version=version, aliases=aliases)

    if repo_info.is_branch():
        current_branch = repo_info.current_branch
        if current_branch is None:
            raise ValueError(
                f"The branch {repo_info.ref_name!r} is not a valid branch name",
            )
        minor: int
        if current_branch.minor is None:
            next_minor = repo_info.find_next_minor_for_major_branch()
            if next_minor is None:
                raise ValueError(
                    f"Could not determine the next minor version for {current_branch.name!r}",
                )
            minor = next_minor
            aliases.append(f"v{current_branch.major}-dev")  # vX-dev
        else:
            minor = current_branch.minor

        major = current_branch.major
        title = f"v{major}.{minor}-dev ({repo_info.sha[:7]})"
        version = f"v{major}.{minor}-dev"  # vX.Y-dev
        if repo_info.is_branch_latest():
            aliases.append("latest-dev")
        return MikeVersionInfo(title=title, version=version, aliases=aliases)

    raise ValueError(
        f"Don't know how to handle '{repo_info.ref}' to make 'mike' version",
    )


_is_version_re = re.compile(r"^v(\d+).(\d+)(-dev|-pre)?$")
_stable_to_semver_re = re.compile(r"^v(\d+).(\d+)$")
_pre_to_semver_re = re.compile(r"^v(\d+).(\d+)-pre$")
_dev_to_semver_re = re.compile(r"^v(\d+).(\d+)-dev$")


def _to_fake_sortable_semver(version: str) -> str:
    """Convert a branch version string to a semver string.

    The following transformations are applied:

    - `vX.Y-pre` -> `X.Y.0-pre`
    - `vX.Y`     -> `X.Y.0`
    - `vX.Y-dev` -> `X.Y.999999`

    The idea is to convert the version string to a semver string that can be sorted
    together with proper semver tags using the semver built-in sorting.

    Args:
        version: The version string to convert.

    Returns:
        The converted version string.
    """
    version = _stable_to_semver_re.sub(r"\1.\2.0", version)
    version = _pre_to_semver_re.sub(r"\1.\2.0-pre", version)
    version = _dev_to_semver_re.sub(r"\1.\2.999999", version)
    if version.startswith("v"):
        version = version[1:]
    return version


def compare_mike_version(version1: str, version2: str) -> int:
    """Compare two versions.

    The versions are compared as follows:

    - Versions are first compared by major version (`X`).
    - If they have the same major, then they are compared by minor version (`Y`).
    - If they have the same major and minor, then stable versions (`vX.Y`) are
      considered bigger than pre-releases (`vX.Y-pre`) and development versions
      (`vX.Y-dev`) are considered bigger than pre-releases.
    - Any other version not matching `vX.Y(-pre|-dev)?` is considered to be bigger than
      the matching versions.
    - Not matching versions are compared alphabetically.

    Example:

        `v1.0-pre` < `v1.0` < `v1.0-dev` < `v1.1` < `v2.0-pre` < `v2.0` < `v2.0-dev`
        < `whatever` < `x`.

    Args:
        version1: The first version to compare.
        version2: The second version to compare.

    Returns:
        A negative number if `version1` is older than `version2`, a positive number if
            `version1` is newer than `version2`, or zero if they are equal.
    """
    is_version_v1 = _is_version_re.match(version1)
    is_version_v2 = _is_version_re.match(version2)
    if is_version_v1 and is_version_v2:
        return semver.Version.parse(_to_fake_sortable_semver(version1)).compare(
            _to_fake_sortable_semver(version2)
        )

    if is_version_v1:  # version2 is not a version
        return -1
    if is_version_v2:  # version1 is not a version
        return 1

    return -1 if version1 < version2 else 1


def sort_mike_versions(versions: list[str], *, reverse: bool = True) -> list[str]:
    """Sort `mike`'s `version.json` file with a custom order.

    The `version` keys are expected as follows:

    - `vX.Y` for stable release versions
    - `vX.Y-pre` for pre-release versions
    - `vX.Y-dev` for development versions
    - Any other arbitrary string for other versions

    The sorting order is as follows:

    - Versions are first sorted by major version (`X`).
    - Inside a major version group, versions are sorted by minor version (`Y`).
    - For the same major and minor version, development versions (`-dev`) considered
      the latest for that major version group, then stable versions, and finally
      pre-release versions (`-pre`).
    - Other versions appear first and are sorted alphabetically.

    The versions are sorted in-place using
    [`compare_mike_version()`][frequenz.repo.config.mkdocs.mike.compare_mike_version].

    Example:

        `z`, `whatever`, `v2.1-dev`, `v2.1`, `v2.1-pre`, `v2.0`, `v1.1-dev`, `v1.0-dev`,
        `v1.0`

    Args:
        versions: The list of versions to sort.
        reverse: Whether to sort in reverse order.

    Returns:
        The sorted list of versions.
    """
    versions.sort(key=functools.cmp_to_key(compare_mike_version), reverse=reverse)
    return versions
