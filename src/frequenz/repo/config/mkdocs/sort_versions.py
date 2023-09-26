# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Sort `mike`'s `version.json` file with a custom order.

The `version` keys are expected as follows:

- `vX` and `vX.Y` for tagged versions
- `vX-dev` and `vX.Y-dev` for development versions
- Any other arbitrary string for other versions

The sorting order is as follows:

- Other versions appear first and are sorted alphabetically between them.
- Development versions appear before tagged versions for the same `vX` and `vX.Y`
   version.
- Regular semver sorting is used within the same tagger or development version.
"""

import functools
import json
import re
import sys
from typing import TypedDict

from semver.version import Version as SemVersion

_is_version_re = re.compile(r"^v(\d+)")
_major_to_semver_re = re.compile(r"^v(\d+)-dev$")
_minor_to_semver_re = re.compile(r"^v(\d+).(\d+)-dev$")
_patch_to_semver_re = re.compile(r"^v(\d+).(\d+)$")


class Version(TypedDict):
    """A version entry in `version.json`."""

    version: str
    """The version string."""

    title: str
    """The version title."""

    aliases: list[str]
    """The version aliases."""


def to_semver(version: str) -> str:
    """Convert a version string to a semver string.

    The following transformations are applied:

    - `vX` -> `vX.9999.9999-zzzz`
    - `vX.Y` -> `vX.Y.9999-zzzz`
    - `vX.Y.Z` -> `vX.Y.Z`

    Args:
        version: The version string to convert.

    Returns:
        The converted version string.
    """
    version = _patch_to_semver_re.sub(r"\1.\2.0", version)
    version = _major_to_semver_re.sub(r"\1.9999.9999-zzzz", version)
    version = _minor_to_semver_re.sub(r"\1.\2.9999-zzzz", version)
    if version.startswith("v"):
        version = version[1:]
    return version


def compare_version(version1: Version, version2: Version) -> int:
    """Compare two versions.

    The versions are first converted to semver strings via `to_semver()` and then
    compared using `semver.version.Version.compare()`.

    If the conversion fails, then non-semver versions are considered to be more recent
    than semver versions. If both versions are non-semver, then they are compared
    alphabetically.

    Args:
        version1: The first version to compare.
        version2: The second version to compare.

    Returns:
        A negative number if `version1` is older than `version2`, a positive number if
        `version1` is newer than `version2`, or zero if they are equal.
    """
    ver1: str = version1["version"]
    ver2: str = version2["version"]
    try:
        # We need the cast because `semver` is not typed
        return SemVersion.parse(to_semver(ver1)).compare(to_semver(ver2))
    except ValueError:
        pass

    is_version_v1 = _is_version_re.match(ver1)
    is_version_v2 = _is_version_re.match(ver2)
    if is_version_v1 and is_version_v2:
        return (ver1 > ver2) - (ver1 < ver2)
    if is_version_v1:
        return -1
    if is_version_v2:
        return 1

    return 0


def sort_versions(versions: list[Version]) -> list[Version]:
    """Sort a list of versions.

    The versions are sorted in-place using `compare_version()`.

    Args:
        versions: The list of versions to sort.

    Returns:
        The sorted list of versions.
    """
    versions.sort(key=functools.cmp_to_key(compare_version), reverse=True)
    return versions


def main() -> None:
    """Sort `mike`'s `version.json` file with a custom order.

    The versions are sorted using `sort_versions()`.

    If no arguments are given, then the contents are read from stdin and the sorted
    versions are printed to stdout.

    If one argument is given, then the contents of the file are replaced with the sorted
    versions.

    If more than one argument is given, then an error is printed to stderr and the
    program exits with a non-zero exit code.
    """
    match len(sys.argv):
        case 1:
            json.dump(json.load(sys.stdin), sys.stdout, separators=(",", ":"))
        case 2:
            with open(sys.argv[1], "r", encoding="utf8") as f_in:
                sorted_versions = sort_versions(json.load(f_in))
            with open(sys.argv[1], "w", encoding="utf8") as f_out:
                json.dump(sorted_versions, f_out, separators=(",", ":"))
        case _:
            print(
                f"""\
Usage: {sys.argv[0]} [<versions.json>]

If <versions.json> is given, the contents will be replaced with the sorted versions.
Otherwise, the contents are read from stdin and the sorted versions are printed to stdout.
""",
                file=sys.stderr,
            )
            sys.exit(2)


if __name__ == "__main__":
    main()
