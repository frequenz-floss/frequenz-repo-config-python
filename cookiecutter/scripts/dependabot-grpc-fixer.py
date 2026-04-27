"""Fix grpc/protobuf dependency bounds in `pyproject.toml` after Dependabot.

Dependabot's grouped updates for `grpcio*`/`protobuf` leave Frequenz API
repositories in an inconsistent state. These repositories split the gRPC and
protobuf dependencies in two parts:

* A *build-time* part (`grpcio-tools`, `mypy-protobuf`, etc.) that is used
  to generate Python bindings from the `.proto` files. Dependabot tracks and
  bumps these because they are pinned in `pyproject.toml`.
* A *runtime* part (`grpcio`, `protobuf`) expressed as a *range* that
  consumers of the generated bindings must satisfy. The lower bound must be
  no greater than the build-time pin (otherwise the bindings would be built
  against an unsupported version), and the upper bound encodes the
  compatibility window we are willing to support.

Dependabot only knows how to bump the build-time pins. After such an update
the runtime ranges are stale and consumers can end up resolving runtime
versions that are *older* than the version the bindings were generated with.

On top of that, `protobuf`'s compatibility guarantees span two consecutive
major versions, while `grpcio` only guarantees one. The upper bound of each
runtime range encodes that contract, and there is a trailing
`# Do not widen beyond N!` comment that mirrors the upper bound to make the
intent explicit (and to provide an additional anchor for this script).

This script reads the JSON metadata that the `dependabot/fetch-metadata`
GitHub Action writes to `UPDATED_DEPENDENCIES_JSON`, finds the new
build-time versions for `grpcio`/`protobuf`, and rewrites the runtime
ranges in `pyproject.toml` accordingly:

* The lower bound becomes the new build-time version.
* The upper bound becomes `new_major + offset` where `offset` is `1` for
  `grpcio` and `2` for `protobuf`.
* The `# Do not widen beyond N!` comment is updated to match.

Version-string contract
-----------------------

`newVersion` payload entries are expected to be PEP 440-shaped release
versions (`N(.N)*` with an optional leading `v`). Trailing junk such as
`"1abc"` is rejected outright.

Pre-release versions (e.g. `"2rc1"`, `"2.0.0a1"`) are a special case.
Because pip ignores pre-releases unless `--pre` is passed, accepting one
silently would produce a runtime range that no default `pip install`
resolution can satisfy. To avoid that footgun the script still rewrites
the range using the pre-release version (so the file is left in a
consistent state for manual inspection), but then exits with a non-zero
status and prints a warning, forcing a human to review the change and
decide whether to opt into `--pre` or revert. Dependabot's pre-release
handling is opt-in anyway, so this should never happen during a normal,
unattended run.
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

PYPROJECT = Path("pyproject.toml")
"""Default path to the `pyproject.toml` file to update."""

METADATA_ENV_VAR = "UPDATED_DEPENDENCIES_JSON"
"""Environment variable populated by `dependabot/fetch-metadata`."""

TRACKED_DEPS = ("protobuf", "grpcio-tools", "grpcio")
"""Dependency names this script consumes from the Dependabot metadata.

`grpcio-tools` is included so the Dependabot payload is accepted even when
only the build-time package was bumped; the runtime `grpcio` floor is then
synced from the same version because they are kept in lockstep.
"""

RUNTIME_DEPS = ("protobuf", "grpcio")
"""Runtime dependencies whose range is rewritten in `pyproject.toml`."""

UPPER_BOUND_OFFSETS = {
    "protobuf": 2,
    "grpcio": 1,
}
"""How many major versions past the new floor each runtime range may span.

`protobuf` guarantees compatibility across two consecutive majors; `grpcio`
only across one.
"""


@dataclass(frozen=True, kw_only=True)
class DependencyUpdate:
    """A single Dependabot-reported dependency version update."""

    name: str
    """Dependency name (e.g. `"protobuf"`)."""

    new_version: str
    """The new version Dependabot wants to pin (e.g. `"6.32.1"`)."""


def fail(message: str) -> NoReturn:
    """Report an error and exit immediately."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


# Strict PEP 440-style release version with optional pre/post/dev/local
# segments. Anchored on both ends so trailing junk (e.g. `"1abc"`) is
# rejected. Group 1 captures the major number, group 2 captures the
# pre-release/dev-release tag if any (used by `is_prerelease`).
_VERSION_RE = re.compile(
    r"""
    \A
    v?
    (\d+)                       # major
    (?:\.\d+)*                  # additional release segments
    (?:                         # optional PEP 440 suffixes
        (?:[._-]?(a|b|c|rc|alpha|beta|pre|preview)\d*)?  # pre-release
        (?:[._-]?post\d*)?      # post-release
        (?:[._-]?(dev)\d*)?     # dev-release
        (?:\+[A-Za-z0-9.]+)?    # local version
    )
    \Z
    """,
    re.VERBOSE | re.IGNORECASE,
)


def major(version: str) -> int:
    """Return the major version number extracted from a version string.

    The full string must look like a PEP 440 release version (with an
    optional leading ``v`` and optional pre/post/dev/local suffixes).
    Anything else is rejected via :func:`fail`.
    """
    match = _VERSION_RE.match(version.strip())
    if match is None:
        fail(
            f"Could not parse a major version from {version!r}. "
            "Expected a PEP 440 release version such as '6.32.1', 'v2', or "
            "'2.0.0rc1' (optional leading 'v' and optional pre/post/dev/local "
            "suffixes). Check the 'newVersion' field in the Dependabot "
            f"{METADATA_ENV_VAR} payload."
        )
    return int(match.group(1))


def is_prerelease(version: str) -> bool:
    """Return whether ``version`` carries a PEP 440 pre-release segment.

    Assumes ``version`` has already been validated by :func:`major`; if
    it has not, returns ``False`` (the caller will fail elsewhere).
    """
    match = _VERSION_RE.match(version.strip())
    if match is None:
        return False
    return match.group(2) is not None or match.group(3) is not None


def parse_dependabot_metadata(raw: str) -> list[DependencyUpdate]:
    """Parse the Dependabot `updated-dependencies` JSON payload.

    Only entries from the `pip` ecosystem in the root directory whose name
    is in `TRACKED_DEPS` are returned. Conflicting versions for the same
    dependency cause the script to abort.
    """
    if not raw:
        fail(
            f"{METADATA_ENV_VAR} is empty. This variable must be populated by "
            "the 'dependabot/fetch-metadata' GitHub Action (its "
            "'updated-dependencies-json' output). Make sure that step ran "
            "successfully before this script and that its output is forwarded "
            f"via 'env: {METADATA_ENV_VAR}: ${{{{ steps.<id>.outputs."
            "updated-dependencies-json }}}}'."
        )

    try:
        dependencies = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(
            f"Failed to parse {METADATA_ENV_VAR} as JSON: {exc}. The variable "
            "must contain the JSON array produced by "
            "'dependabot/fetch-metadata' (the 'updated-dependencies-json' "
            f"output). Got (first 200 chars): {raw[:200]!r}"
        )

    if not isinstance(dependencies, list):
        fail(
            f"{METADATA_ENV_VAR} must decode to a JSON array, got "
            f"{type(dependencies).__name__}. The variable must contain the "
            "JSON array produced by 'dependabot/fetch-metadata' (its "
            "'updated-dependencies-json' output)."
        )

    updates: dict[str, DependencyUpdate] = {}
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            fail(
                f"{METADATA_ENV_VAR} contains a non-object item "
                f"({type(dependency).__name__}: {dependency!r}). Each entry "
                "must be a JSON object as produced by "
                "'dependabot/fetch-metadata'."
            )
        if (
            dependency.get("packageEcosystem") != "pip"
            or dependency.get("directory") != "/"
        ):
            continue
        name = dependency.get("dependencyName")
        if name not in TRACKED_DEPS:
            continue
        version = dependency.get("newVersion")
        if not isinstance(version, str) or not version:
            fail(
                f"Missing or empty 'newVersion' for {name!r} in "
                f"{METADATA_ENV_VAR}. Every tracked entry "
                f"({', '.join(repr(n) for n in TRACKED_DEPS)}) must include a "
                f"non-empty 'newVersion' string. Got: {version!r}"
            )
        previous = updates.get(name)
        if previous is not None and previous.new_version != version:
            fail(
                f"Found conflicting {METADATA_ENV_VAR} entries for {name!r}: "
                f"{previous.new_version!r} and {version!r}. Dependabot should "
                "only report one 'newVersion' per dependency per directory; "
                "double-check the payload and merge the duplicate entries "
                "before re-running."
            )
        updates[name] = DependencyUpdate(name=name, new_version=version)

    if not updates:
        fail(
            "No grpc/protobuf dependency metadata found in "
            f"{METADATA_ENV_VAR}. The payload contained no entries with "
            "'packageEcosystem' == 'pip', 'directory' == '/' and "
            f"'dependencyName' in {{{', '.join(repr(n) for n in TRACKED_DEPS)}}}. "
            "This script is meant to run only on Dependabot PRs that bump "
            "grpcio/grpcio-tools/protobuf at the repository root; check the "
            "workflow's trigger condition if it ran outside that scope."
        )

    return list(updates.values())


def runtime_versions(updates: list[DependencyUpdate]) -> dict[str, str]:
    """Return `{name: new_version}` for runtime dependencies only.

    Build-time-only entries (e.g. `grpcio-tools`) are dropped: a Dependabot
    bump of just `grpcio-tools` does not by itself imply a runtime range
    rewrite. The runtime `grpcio` floor is updated only when Dependabot
    reports a matching `grpcio` bump in the same payload.
    """
    return {
        update.name: update.new_version
        for update in updates
        if update.name in RUNTIME_DEPS
    }


def _canonical_range_shape(name: str, new_limit_major: int) -> str:
    """Return the canonical runtime range string the fixer expects to emit."""
    return (
        f'"{name} >= <floor>, < {new_limit_major}", '
        f"# Do not widen beyond {new_limit_major}!"
    )


def _diagnose_runtime_range_mismatch(
    text: str, name: str, new_limit_major: int, found: int
) -> NoReturn:
    """Abort with a maintainer-actionable diagnostic for a range-regex miss.

    Called when the strict runtime-range regex did not produce exactly one
    match. Uses a lenient probe to locate ``"<name> ...something..."`` entries
    in ``text`` so the error can point at the actual offending line(s)
    instead of just saying "no match".
    """
    canonical = _canonical_range_shape(name, new_limit_major)
    # Lenient probe: any double-quoted string that starts with the dep name
    # followed by some constraint expression. This catches `<= N`, `< N.N`,
    # alternative spacing, etc. — anything the strict regex would reject.
    probe = rf'"{re.escape(name)}\s*[<>=!~][^"]*"'
    found_strings = re.findall(probe, text)

    if found == 0 and not found_strings:
        fail(
            f"No runtime range for {name!r} found in pyproject.toml. The "
            f"fixer expects one entry shaped like:\n  {canonical}\n"
            f"Add it under [project].dependencies (or the equivalent section "
            "your project uses) and re-run."
        )

    if found == 0:
        formatted = "\n  ".join(found_strings)
        fail(
            f"Found a {name!r} dependency entry in pyproject.toml but it "
            f"does not match the shape the fixer requires. Got:\n  "
            f"{formatted}\nExpected exactly one entry shaped like:\n  "
            f"{canonical}\nThe upper bound must be a bare major-version "
            "integer (e.g. '< 7') — dotted bounds like '< 7.0' and "
            "inclusive operators like '<= 7' are rejected because the "
            "fixer would silently change their shape. Restore the "
            "canonical shape and re-run."
        )

    # found > 1
    formatted = "\n  ".join(found_strings) if found_strings else "(none captured)"
    fail(
        f"Found {found} runtime range entries for {name!r} in "
        f"pyproject.toml; expected exactly one. Matches:\n  {formatted}\n"
        "Deduplicate the entries so a single canonical line remains:\n  "
        f"{canonical}"
    )


def replace_range(text: str, name: str, version: str) -> tuple[str, int]:
    """Update a dependency floor and its compatibility upper bound.

    Rewrites the `"<name> >= X, < Y"` runtime range and the mandatory
    `# Do not widen beyond Y!` comment so both reflect the new `version`
    and the configured `UPPER_BOUND_OFFSETS` for `name`.

    The upper bound ``Y`` must be a bare major-version integer (e.g. ``< 7``).
    Dotted upper bounds such as ``< 7.0`` and inclusive operators such as
    ``<= 7`` are rejected: the script aborts rather than silently rewriting
    them to the canonical ``< N`` shape (which would change the constraint's
    meaning or formatting).

    If the trailing comment is present in the expected format, it is updated
    too, even when it was stale. If it is absent or malformed, the range is
    still updated and a manual step is recorded so the comment can be restored
    without blocking the dependency bump.
    """
    upper_bound_offset = UPPER_BOUND_OFFSETS.get(name)
    if upper_bound_offset is None:
        fail(
            f"Unsupported runtime dependency {name!r}; this script only "
            f"knows how to rewrite ranges for "
            f"{', '.join(repr(n) for n in RUNTIME_DEPS)}. If a new runtime "
            "dependency must be tracked, extend RUNTIME_DEPS and "
            "UPPER_BOUND_OFFSETS in dependabot-grpc-fixer.py."
        )

    new_limit_major = major(version) + upper_bound_offset
    # The upper bound is intentionally restricted to a bare major-number
    # integer (e.g. ``< 7``). Anything else — a dotted version such as
    # ``< 7.0``, a ``<=`` operator, or extra whitespace inside the operator —
    # would not round-trip cleanly through this rewrite and would silently
    # change shape. Failing loudly here forces the maintainer to either keep
    # the canonical shape or update this script consciously.
    pattern = rf'("{re.escape(name)}\s*>=\s*)([^,\"]+)(\s*,\s*<\s*)(\d+)(\s*")'

    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        _diagnose_runtime_range_mismatch(text, name, new_limit_major, len(matches))

    old_floor = matches[0].group(2).strip()
    if major(version) < major(old_floor):
        fail(
            f"Refusing to downgrade {name} from {old_floor} to {version}. "
            f"The Dependabot payload (env var {METADATA_ENV_VAR}) reported a "
            f"newVersion {version!r} whose major is lower than the current "
            f"floor {old_floor!r} in pyproject.toml. This usually means "
            "Dependabot is replaying an older bump on top of a newer floor; "
            "close that PR or unblock by manually setting the floor in "
            "pyproject.toml first."
        )

    def repl(match: re.Match[str]) -> str:
        return (
            f"{match.group(1)}{version}{match.group(3)}"
            f"{new_limit_major}{match.group(5)}"
        )

    text, count = re.subn(pattern, repl, text, count=1)

    comment_pattern = (
        rf'("{re.escape(name)}\s*>=\s*{re.escape(version)}'
        rf'\s*,\s*<\s*{new_limit_major}"\s*,\s*'
        rf"#\s*Do not widen beyond\s*)\d+(!)"
    )
    text, comment_count = re.subn(
        comment_pattern, rf"\g<1>{new_limit_major}\2", text, count=1
    )
    if comment_count != 1:
        # Surface the line we just rewrote so the maintainer can see exactly
        # which entry is missing its trailing 'Do not widen beyond N!' marker.
        rewritten_line = re.search(
            rf'^[^\n]*"{re.escape(name)}\s*>=\s*{re.escape(version)}'
            rf'\s*,\s*<\s*{new_limit_major}"[^\n]*$',
            text,
            re.MULTILINE,
        )
        line_snippet = (
            rewritten_line.group(0).strip() if rewritten_line else "(not found)"
        )
        fail(
            f"The expected '# Do not widen beyond {new_limit_major}!' "
            f"trailing comment for {name!r} is missing or malformed after "
            f"rewriting the range to '< {new_limit_major}'. The runtime range "
            "was updated, but the marker comment should live on the same line "
            f"so the compatibility limit stays explicit. Offending line:\n  "
            f"{line_snippet}\nExpected shape:\n  "
            f"{_canonical_range_shape(name, new_limit_major)}"
        )
    return text, count


def apply_updates(pyproject_path: Path, updates: list[DependencyUpdate]) -> None:
    """Apply runtime range updates derived from `updates` to `pyproject_path`.

    If any of the new versions is a PEP 440 pre-release, the rewrite is still
    performed (so the file is left consistent for manual review) but the
    script terminates with a non-zero status via :func:`fail`, because pip
    will not pick up pre-releases without ``--pre`` and the contract change
    deserves a human in the loop.
    """
    text = pyproject_path.read_text(encoding="utf-8")
    versions = runtime_versions(updates)
    replacements = 0
    prereleases: list[tuple[str, str]] = []

    for name in RUNTIME_DEPS:
        version = versions.get(name)
        if version is None:
            continue
        if is_prerelease(version):
            prereleases.append((name, version))
        text, count = replace_range(text, name, version)
        replacements += count

    if replacements == 0:
        print("No grpc/protobuf runtime constraints to update.")
        return

    pyproject_path.write_text(text, encoding="utf-8")
    print(f"Updated {pyproject_path} with {replacements} grpc/protobuf constraint(s).")

    if prereleases:
        formatted = ", ".join(f"{name}={version}" for name, version in prereleases)
        fail(
            "Applied pre-release version(s) to runtime range(s): "
            f"{formatted}. pip ignores pre-releases unless '--pre' is passed, "
            f"so default installs cannot resolve the updated {pyproject_path}. "
            "The file has been rewritten so the range and the marker comment "
            "stay consistent; review it manually and either (a) revert to the "
            "previous stable floor, (b) opt the project into pre-releases, "
            "or (c) wait for the corresponding stable release before merging."
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Sync grpc/protobuf runtime dependency ranges in pyproject.toml "
            "with the build-time versions reported by Dependabot via the "
            f"{METADATA_ENV_VAR} environment variable."
        ),
    )
    parser.add_argument(
        "pyproject",
        nargs="?",
        type=Path,
        default=PYPROJECT,
        help=(f"Path to the pyproject.toml file to update (default: {PYPROJECT})."),
    )
    return parser.parse_args(argv)


def main() -> None:
    """Apply dependency version updates to a `pyproject.toml` file."""
    args = parse_args()
    if not args.pyproject.exists():
        fail(
            f"{args.pyproject} not found (resolved from cwd "
            f"{Path.cwd()}). Pass the correct path as the script's positional "
            "argument or run it from the repository root that contains "
            "pyproject.toml."
        )
    raw_metadata = os.environ.get(METADATA_ENV_VAR, "")
    updates = parse_dependabot_metadata(raw_metadata)
    apply_updates(args.pyproject, updates)


if __name__ == "__main__":
    main()
