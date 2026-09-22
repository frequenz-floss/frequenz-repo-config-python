#!/usr/bin/env python3
# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Script to migrate existing projects to new versions of the cookiecutter template.

This script migrates existing projects to new versions of the cookiecutter
template, removing the need to completely regenerate the project from
scratch.

To run it, the simplest way is to fetch it from GitHub and run it directly:

    curl -sSLf https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3

Make sure to replace the `<tag>` to the version you want to migrate to in the URL.

For jumping multiple versions you should run the script multiple times, once
for each version.

And remember to follow any manual instructions for each run.
"""  # noqa: E501

# R0801 is similarity detection, as the template is always similar to the current script
# pylint: disable=too-many-lines, too-many-locals, too-many-branches, too-many-statements, R0801

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, SupportsIndex

_manual_steps: list[str] = []  # pylint: disable=invalid-name


def main() -> None:
    """Run the migration steps."""
    # Add a separation line like this one after each migration step.
    print("=" * 72)
    print("Fixing the location of the mkdocstrings `paths` key in mkdocs.yml...")
    migrate_mkdocstrings_paths()
    print("=" * 72)
    print("Adding the griffe-warnings-deprecated dependency...")
    migrate_griffe_warnings_deprecated_dependency()
    print("=" * 72)
    print("Enabling the griffe-warnings-deprecated extension in mkdocs.yml...")
    migrate_griffe_warnings_deprecated_extension()
    print("=" * 72)
    print("Adding the `Deprecated` admonition style to mkdocstrings.css...")
    migrate_deprecated_admonition_css()
    print("=" * 72)
    print("Converting deprecation admonitions and finding the undocumented ones...")
    migrate_deprecation_admonitions()
    print("=" * 72)
    print()

    if _manual_steps:
        print(
            "\033[5;33m⚠️⚠️⚠️\033[0;33m Remember to check the manual steps: \033[5;33m⚠️⚠️⚠️\033[0m"
        )
        for n, step in enumerate(_manual_steps, start=1):
            print(f"\033[5;33m⚠️⚠️⚠️   \033[0;33m{n}. {step}\033[0m")
        print()

        print(
            "\033[5;31m❌\033[0;31m Migration script finished but requires manual "
            "intervention \033[5;31m❌\033[0m"
        )
        print()

        sys.exit(len(_manual_steps))

    print("\033[0;32m       ✅ Migration script finished successfully ✅\033[0m")
    print()


def apply_patch(patch_content: str) -> None:
    """Apply a patch using the patch utility."""
    subprocess.run(["patch", "-p1"], input=patch_content.encode(), check=True)


def replace_file_atomically(  # noqa; DOC501, DOC503
    filepath: str | Path, new_content: str
) -> None:
    """Replace a file atomically with the given content.

    The replacement is done atomically by writing to a temporary file in the
    same directory and then moving it to the target location.

    Args:
        filepath: The path to the file to replace.
        new_content: The content to write to the file.
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    tmp_dir = filepath.parent
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # pylint: disable-next=consider-using-with
    tmp = tempfile.NamedTemporaryFile(mode="w", dir=tmp_dir, delete=False)

    try:
        st = None
        try:
            st = os.stat(filepath)
        except FileNotFoundError:
            st = None

        tmp.write(new_content)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()

        if st is not None:
            os.chmod(tmp.name, st.st_mode)

        os.replace(tmp.name, filepath)

    except BaseException:
        tmp.close()
        os.unlink(tmp.name)
        raise


def replace_file_contents_atomically(  # noqa; DOC501
    filepath: str | Path,
    old: str,
    new: str,
    count: SupportsIndex = -1,
    *,
    content: str | None = None,
) -> None:
    """Replace a file atomically with new content.

    The replacement is done atomically by writing to a temporary file and
    then moving it to the target location.

    Args:
        filepath: The path to the file to replace.
        old: The string to replace.
        new: The string to replace it with.
        count: The maximum number of occurrences to replace. If negative, all occurrences are
            replaced.
        content: The content to replace. If not provided, the file is read from disk.
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    if content is None:
        content = filepath.read_text(encoding="utf-8")

    replace_file_atomically(filepath, content.replace(old, new, count))


def calculate_file_sha256_skip_lines(filepath: Path, skip_lines: int) -> str | None:
    """Calculate SHA256 of file contents excluding the first N lines.

    Args:
        filepath: Path to the file to hash
        skip_lines: Number of lines to skip at the beginning

    Returns:
        The SHA256 hex digest, or None if the file doesn't exist
    """
    if not filepath.exists():
        return None

    # Read file and normalize line endings to LF
    content = filepath.read_text(encoding="utf-8").replace("\r\n", "\n")
    # Skip first N lines and ensure there's a trailing newline
    remaining_content = "\n".join(content.splitlines()[skip_lines:]) + "\n"
    return hashlib.sha256(remaining_content.encode()).hexdigest()


def find_ruleset(name: str) -> dict[str, Any] | None:
    """Find a repository ruleset by name using the GitHub API.

    Args:
        name: The name of the ruleset to search for.

    Returns:
        The ruleset summary dict (id, name, …) if found, or ``None`` if not
        found or if the API call failed (a diagnostic is printed in the latter
        case).
    """
    try:
        stdout = subprocess.check_output(
            ["gh", "api", "repos/:owner/:repo/rulesets"],
            text=True,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        print("  gh CLI not found; cannot query rulesets via the GitHub API.")
        return None
    except subprocess.CalledProcessError as exc:
        print(f"  Failed to list rulesets: {exc.stderr.strip()}")
        return None

    rulesets: list[dict[str, Any]] = json.loads(stdout)
    return next((r for r in rulesets if r.get("name") == name), None)


def get_ruleset(ruleset: str | int) -> dict[str, Any] | None:
    """Fetch the full details of a repository ruleset by name or ID.

    Args:
        ruleset: The ruleset name (``str``) or numeric ruleset ID (``int``).

    Returns:
        The full ruleset dict, or ``None`` if the ruleset could not be found
        or the API call failed (a diagnostic is printed).
    """
    ruleset_id = ruleset
    if isinstance(ruleset, str):
        entry = find_ruleset(ruleset)
        if entry is None:
            return None
        ruleset_id = entry["id"]

    try:
        stdout = subprocess.check_output(
            ["gh", "api", f"repos/:owner/:repo/rulesets/{ruleset_id}"],
            text=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        print(f"  Failed to fetch ruleset {ruleset_id}: {exc.stderr.strip()}")
        return None

    return json.loads(stdout)  # type: ignore[no-any-return]


def update_ruleset(ruleset_id: int, config: dict[str, Any]) -> bool:
    """Update a repository ruleset via the GitHub API.

    Only ``name``, ``target``, ``enforcement``, ``conditions``, ``rules``,
    and ``bypass_actors`` are sent (explicit allowlist to avoid sending
    read-only fields back to the API).

    Args:
        ruleset_id: The numeric ruleset ID to update.
        config: The full ruleset dict (as returned by :func:`get_ruleset`)
            with the desired changes already applied in-memory.

    Returns:
        ``True`` on success, ``False`` if the API call failed (a diagnostic
        is printed).
    """
    payload: dict[str, Any] = {
        "name": config["name"],
        "target": config["target"],
        "enforcement": config["enforcement"],
        "conditions": config["conditions"],
        "rules": config["rules"],
    }
    if "bypass_actors" in config:
        payload["bypass_actors"] = config["bypass_actors"]

    try:
        subprocess.check_output(
            [
                "gh",
                "api",
                "-X",
                "PUT",
                f"repos/:owner/:repo/rulesets/{ruleset_id}",
                "--input",
                "-",
            ],
            input=json.dumps(payload),
            text=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        print(f"  Failed to update ruleset {ruleset_id}: {exc.stderr.strip()}")
        return False

    return True


def get_ruleset_settings_url() -> str | None:
    """Return the URL to the repository's ruleset settings page.

    Returns:
        The URL as a string, or ``None`` if it could not be determined.
    """
    try:
        stdout = subprocess.check_output(
            ["gh", "repo", "view", "--json", "owner,name"],
            text=True,
            stderr=subprocess.PIPE,
        )
        info: dict[str, Any] = json.loads(stdout)
        org = info["owner"]["login"]
        repo = info["name"]
        return f"https://github.com/{org}/{repo}/settings/rules"
    except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError):
        return None


def read_cookiecutter_str_var(name: str) -> str | None:
    """Read a cookiecutter variable from the replay file."""
    replay_path = Path(".cookiecutter-replay.json")
    if not replay_path.exists():
        return None

    try:
        data = json.loads(replay_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    cookiecutter_data = data.get("cookiecutter")
    if not isinstance(cookiecutter_data, dict):
        return None

    value = cookiecutter_data.get(name)
    if not isinstance(value, str):
        return None

    return value


def migrate_mkdocstrings_paths() -> None:
    """Move the mkdocstrings `paths` key under the `python` handler.

    The key belongs to `plugins.mkdocstrings.handlers.python.paths`, but two
    older versions of the template put it elsewhere:

    * Inside `handlers.python.options`, where mkdocstrings ignores it, so the
      source tree is never added to `sys.path`.
    * Directly under `handlers`, where mkdocstrings reads it as a handler name
      and aborts the build with `ModuleNotFoundError: No module named
      'mkdocstrings_handlers.paths'`.

    Both are rewritten to the correct location, and a file that already has it
    there is left untouched. A missing `mkdocs.yml` or a missing `handlers`
    block is reported as a manual step, since every project is expected to have
    both.
    """
    mkdocs_yml = Path("mkdocs.yml")
    handlers_key = "      handlers:"
    python_key = "        python:"
    # Under `handlers` and inside `handlers.python.options`, respectively.
    bad_paths_keys = ("        paths:", "            paths:")

    if not mkdocs_yml.exists():
        manual_step(
            f"{mkdocs_yml} does not exist. Every project should have one; "
            "please check why it is missing and make sure the mkdocstrings "
            "`paths` key sits under `handlers.python`."
        )
        return

    try:
        lines = mkdocs_yml.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError as exc:
        manual_step(
            f"Failed to read {mkdocs_yml}: {exc}. Please make sure the "
            "mkdocstrings `paths` key sits under `handlers.python` manually."
        )
        return

    handlers_index = next(
        (i for i, line in enumerate(lines) if line.startswith(handlers_key)), None
    )
    if handlers_index is None:
        manual_step(
            f"{mkdocs_yml} has no mkdocstrings `handlers` configuration. Every "
            "project should have one; please check why it is missing and make "
            "sure the `paths` key sits under `handlers.python`."
        )
        return

    # The handlers block ends at the first non-blank line indented at most as
    # much as the `handlers:` key itself.
    block_end = len(lines)
    for index in range(handlers_index + 1, len(lines)):
        line = lines[index]
        if line.strip() and len(line) - len(line.lstrip()) <= 6:
            block_end = index
            break
    block = range(handlers_index + 1, block_end)

    bad_index = next(
        (i for i in block if lines[i].startswith(bad_paths_keys)),
        None,
    )
    if bad_index is None:
        print(f"  Skipped {mkdocs_yml}: `paths` key already in the right place")
        return

    python_index = next((i for i in block if lines[i].startswith(python_key)), None)
    if python_index is None:
        manual_step(
            f"{mkdocs_yml} has a misplaced `paths` key but no `python` handler; "
            "please move the key manually."
        )
        return

    paths_value = lines[bad_index].split(":", 1)[1].strip()
    if not paths_value:
        manual_step(
            f"The `paths` key in {mkdocs_yml} spans several lines; please move "
            "it under the `python` handler manually."
        )
        return

    del lines[bad_index]
    if bad_index < python_index:
        python_index -= 1
    lines.insert(python_index + 1, f"          paths: {paths_value}\n")

    try:
        replace_file_atomically(mkdocs_yml, "".join(lines))
        print(f"  Updated {mkdocs_yml}: moved `paths` under the `python` handler")
    except OSError as exc:
        manual_step(
            f"Failed to update {mkdocs_yml}: {exc}. Please move the "
            "mkdocstrings `paths` key under `handlers.python` manually."
        )


_GRIFFE_WARNINGS_DEPRECATED_REQUIREMENT = '"griffe-warnings-deprecated == 1.1.1",'
"""The ``dev-mkdocs`` requirement added by the migration."""

# The icon is `material/grave-stone`, from the set shipped by mkdocs-material.
# It is kept in its own constant because the data URI is far too long for one
# source line.
_DEPRECATED_ADMONITION_ICON = (
    "url('data:image/svg+xml;charset=utf-8,"
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<path d="M10 2h4c3.31 0 5 2.69 5 6v10.66C16.88 17.63 15.07 17 12 17s-4.88'
    ".63-7 1.66V8c0-3.31 1.69-6 5-6M8 8v1.5h8V8zm1 4v1.5h6V12zM3 22v-.69"
    "c2.66-1.69 10.23-5.47 18-.06V22z\"/></svg>')"
)

# Braces are doubled because this is an f-string; the rendered CSS has single
# braces, and must match the template byte for byte.
_DEPRECATED_ADMONITION_CSS = f"""
/* A "Deprecated" admonition, styled like a warning but with its own icon. */
:root {{
  --md-admonition-icon--deprecated: {_DEPRECATED_ADMONITION_ICON};
}}

.md-typeset .admonition.deprecated,
.md-typeset details.deprecated {{
  border-color: #cc9900;
}}

.md-typeset .deprecated > .admonition-title,
.md-typeset .deprecated > summary {{
  background-color: #cc99001a;
}}

.md-typeset .deprecated > .admonition-title::before,
.md-typeset .deprecated > summary::before {{
  background-color: #cc9900;
  -webkit-mask-image: var(--md-admonition-icon--deprecated);
  mask-image: var(--md-admonition-icon--deprecated);
}}
"""

_ADMONITION_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<kind>[A-Za-z][A-Za-z0-9_ ]*):(?P<title>.*?)\s*$"
)
"""A Google-style docstring section header, as griffe parses admonitions."""

_DEPRECATED_ADMONITION_RE = re.compile(r"^(?P<indent>[ \t]*)Deprecated:[ \t]*$")
"""A `Deprecated:` admonition header, written the way it should be."""

_DEPRECATION_MENTION_RE = re.compile(r"deprecat", re.IGNORECASE)
"""Any mention of a deprecation, however it is worded."""

_DEPRECATION_HELPERS = frozenset({"deprecated_member"})
"""Helpers that deprecate a symbol the `deprecated` decorator cannot reach.

`frequenz.core.enum.deprecated_member` marks an enum member, and nothing
renders its message, so the member's docstring is the only place a reader can
learn that it is deprecated. A call to one is worth reporting even though it
says nothing in prose.
"""

_DEPRECATIONS_GUIDE_URL = (
    "https://github.com/frequenz-floss/docs/blob/v0.x.x/python/deprecations.md"
)
"""The guide on how deprecations are marked and documented at Frequenz."""

_SKIPPED_DIRS = frozenset({"__pycache__", "build", "dist", "node_modules", "site"})
"""Directory names never searched for Python sources."""

_TEST_FILE_RE = re.compile(r"^(conftest|test_.+|.+_test)\.py$")
"""A file holding tests rather than documented code."""

_THIS_SCRIPT = Path(__file__).resolve() if "__file__" in globals() else None
"""This script, when it was run from a file rather than piped into `python3`.

A checked out copy of this script is itself full of the word "deprecated", so
it is skipped entirely.
"""

_MAX_MENTIONS_PER_FILE = 10
"""How many mentions of a deprecation are reported for a single file.

A module that implements deprecation support, rather than one that deprecates
something, says the word on nearly every line and would bury the rest of the
report under itself.
"""


@dataclass
class _DeprecationReport:
    """The deprecations a scan of the sources leaves for a human to deal with."""

    duplicated: list[str] = field(default_factory=list)
    """Admonitions on a symbol that a `deprecated` decorator already marks."""

    ambiguous: list[str] = field(default_factory=list)
    """Admonitions that are not a plain `Warning: Deprecated`."""

    unrendered: list[str] = field(default_factory=list)
    """Symbols a helper deprecates without the documentation showing it."""

    unmarked: list[str] = field(default_factory=list)
    """Docstrings talking about a deprecation that nothing marks as one."""


@dataclass(frozen=True, kw_only=True)
class _Docstring:
    """A docstring found in a source, and how its symbol is marked."""

    start: int
    """The line the docstring starts at."""

    end: int
    """The line the docstring ends at."""

    name: str
    """The qualified name of the symbol it documents."""

    decorated: bool = False
    """Whether that symbol carries a `deprecated` decorator."""

    helper_line: int | None = None
    """Where a helper from `_DEPRECATION_HELPERS` deprecates that symbol."""


def migrate_griffe_warnings_deprecated_dependency() -> None:
    """Add ``griffe-warnings-deprecated`` to the ``dev-mkdocs`` dependencies.

    The griffe extension turns the message of a
    `typing_extensions.deprecated` decorator into a `Deprecated:` admonition
    in the rendered documentation, so it is only needed to build the docs.

    The step is skipped when the requirement is already there, which is the
    case for projects that adopted the styling by hand before this release.
    """
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        manual_step(
            f"{pyproject} was not found. Please add "
            f"`{_GRIFFE_WARNINGS_DEPRECATED_REQUIREMENT}` to the `dev-mkdocs` "
            "optional dependencies manually."
        )
        return

    try:
        content = pyproject.read_text(encoding="utf-8")
    except OSError as exc:
        manual_step(
            f"Failed to read {pyproject}: {exc}. Please add "
            f"`{_GRIFFE_WARNINGS_DEPRECATED_REQUIREMENT}` to the `dev-mkdocs` "
            "optional dependencies manually."
        )
        return

    if "griffe-warnings-deprecated" in content:
        print(f"  Skipped {pyproject}: griffe-warnings-deprecated already present")
        return

    section = re.search(r"(?ms)^dev-mkdocs\s*=\s*\[\n(?P<entries>.*?)^\]", content)
    if section is None:
        manual_step(
            f"No `dev-mkdocs` dependency group found in {pyproject}. Please add "
            f"`{_GRIFFE_WARNINGS_DEPRECATED_REQUIREMENT}` to the group that "
            "installs the documentation tooling manually."
        )
        return

    entries = section["entries"].splitlines(keepends=True)
    indent = next(
        (
            entry[: len(entry) - len(entry.lstrip())]
            for entry in entries
            if entry.lstrip().startswith('"')
        ),
        "  ",
    )
    # The generated list is sorted by raw string, so `Markdown` sorts before
    # `black`; inserting with the same comparison keeps migrated projects
    # identical to freshly generated ones.
    position = next(
        (
            index
            for index, entry in enumerate(entries)
            if entry.lstrip().startswith('"')
            and entry.strip() > _GRIFFE_WARNINGS_DEPRECATED_REQUIREMENT
        ),
        len(entries),
    )
    entries.insert(position, f"{indent}{_GRIFFE_WARNINGS_DEPRECATED_REQUIREMENT}\n")

    new_content = (
        content[: section.start("entries")]
        + "".join(entries)
        + content[section.end("entries") :]
    )

    try:
        replace_file_atomically(pyproject, new_content)
        print(f"  Updated {pyproject}: added griffe-warnings-deprecated to dev-mkdocs")
    except OSError as exc:
        manual_step(
            f"Failed to update {pyproject}: {exc}. Please add "
            f"`{_GRIFFE_WARNINGS_DEPRECATED_REQUIREMENT}` to the `dev-mkdocs` "
            "optional dependencies manually."
        )


def migrate_griffe_warnings_deprecated_extension() -> None:
    """Wire the griffe extension into the mkdocstrings handler in ``mkdocs.yml``.

    The extension is configured with `kind: deprecated` and
    `title: Deprecated` so the generated admonition matches the hand-written
    `Deprecated:` ones and picks up the same CSS.

    The step is skipped when the extension is already configured, and a manual
    step is emitted when the mkdocstrings handler options cannot be found.
    """
    mkdocs = Path("mkdocs.yml")
    manual_hint = (
        "Please add the extension manually to the mkdocs.yml file under "
        "plugins.mkdocstrings.handlers.python.options.extensions:\n"
        "\t- griffe_warnings_deprecated:\n"
        "\t    kind: deprecated\n"
        "\t    title: Deprecated"
    )

    if not mkdocs.exists():
        manual_step(f"{mkdocs} was not found. {manual_hint}")
        return

    try:
        content = mkdocs.read_text(encoding="utf-8")
    except OSError as exc:
        manual_step(f"Failed to read {mkdocs}: {exc}. {manual_hint}")
        return

    if "griffe_warnings_deprecated" in content:
        print(f"  Skipped {mkdocs}: the extension is already configured")
        return

    lines = content.splitlines(keepends=True)
    options_index = None
    in_mkdocstrings = False
    for index, line in enumerate(lines):
        if re.match(r"^\s*-\s+mkdocstrings:\s*$", line):
            in_mkdocstrings = True
        elif in_mkdocstrings and re.match(r"^\s*options:\s*$", line):
            options_index = index
            break

    if options_index is None:
        manual_step(
            f"No mkdocstrings handler `options:` found in {mkdocs}. {manual_hint}"
        )
        return

    options_line = lines[options_index]
    indent = options_line[: len(options_line) - len(options_line.lstrip())]
    lines.insert(
        options_index + 1,
        f"{indent}  extensions:\n"
        f"{indent}  - griffe_warnings_deprecated:\n"
        f"{indent}      kind: deprecated\n"
        f"{indent}      title: Deprecated\n",
    )

    try:
        replace_file_atomically(mkdocs, "".join(lines))
        print(f"  Updated {mkdocs}: enabled the griffe_warnings_deprecated extension")
    except OSError as exc:
        manual_step(f"Failed to update {mkdocs}: {exc}. {manual_hint}")


def migrate_deprecated_admonition_css() -> None:
    """Style the `Deprecated:` admonition in ``docs/_css/mkdocstrings.css``.

    Both the extension and the hand-written admonitions render with
    `class="deprecated"`, so this single rule styles them identically: like a
    warning, but with a grave stone icon and its own colour.

    The step is skipped when the rule is already there, which is the case for
    projects that adopted the styling by hand before this release.
    """
    css = Path("docs/_css/mkdocstrings.css")
    manual_hint = (
        "Please add the `Deprecated` admonition style to your mkdocstrings CSS "
        f"manually:\n\n{_DEPRECATED_ADMONITION_CSS}\n"
    )

    if not css.exists():
        manual_step(f"{css} was not found. {manual_hint}")
        return

    try:
        content = css.read_text(encoding="utf-8")
    except OSError as exc:
        manual_step(f"Failed to read {css}: {exc}. {manual_hint}")
        return

    if "--md-admonition-icon--deprecated" in content:
        print(f"  Skipped {css}: the `Deprecated` admonition is already styled")
        return

    if content and not content.endswith("\n"):
        content += "\n"

    try:
        replace_file_atomically(css, content + _DEPRECATED_ADMONITION_CSS)
        print(f"  Updated {css}: added the `Deprecated` admonition style")
    except OSError as exc:
        manual_step(f"Failed to update {css}: {exc}. {manual_hint}")


def migrate_deprecation_admonitions() -> None:
    """Convert hand-written deprecation admonitions, and report the rest.

    Deprecations are now surfaced as a `Deprecated:` admonition, never as
    `Warning: Deprecated`, because a title replaces the word "Deprecated" in
    the rendered output.  A plain `Warning: Deprecated` maps to `Deprecated:`
    without touching the body, so it is converted automatically.

    Two cases are reported instead of being guessed at: an admonition on a
    symbol that also carries a `typing_extensions.deprecated` decorator, which
    must be deleted rather than rewritten because the griffe extension now
    generates one, and any other variant, such as `Note: Deprecated` or a
    custom title, where only a human can tell what was meant.

    Whatever is left is found by searching the docstrings for the word
    "deprecated" itself, since most projects announce their deprecations as
    plain prose that no parser can recognize.
    """
    converted_total = 0
    report = _DeprecationReport()

    for path in _iter_python_files(Path(".")):
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            manual_step(
                f"Failed to read {path}: {exc}. Please replace its "
                "`Warning: Deprecated` admonitions with `Deprecated:` manually."
            )
            continue

        try:
            tree = ast.parse(content)
        except (SyntaxError, ValueError) as exc:
            # A file that never says the word has nothing to convert anyway,
            # and cookiecutter templates that only look like Python are
            # common enough to be worth not complaining about.
            if _DEPRECATION_MENTION_RE.search(content):
                manual_step(
                    f"Failed to parse {path}: {exc}. Please replace its "
                    "`Warning: Deprecated` admonitions with `Deprecated:` "
                    "manually."
                )
            continue

        new_content, converted = _convert_deprecation_admonitions(
            path, content, tree, report
        )
        if new_content is None:
            continue

        try:
            replace_file_atomically(path, new_content)
        except OSError as exc:
            manual_step(
                f"Failed to update {path}: {exc}. Please replace its "
                "`Warning: Deprecated` admonitions with `Deprecated:` manually."
            )
            continue

        converted_total += converted
        print(f"  Updated {path}: converted {converted} deprecation admonition(s)")

    if converted_total == 0:
        print("  No `Warning: Deprecated` admonitions found to convert")

    if report.duplicated:
        manual_step(
            "These symbols carry both a `deprecated` decorator and a "
            "hand-written admonition, so the documentation would now show two. "
            "Please delete the hand-written one, moving anything it says that "
            "the decorator message does not into the decorator message:\n"
            + _indented_list(report.duplicated)
        )

    if report.ambiguous:
        manual_step(
            "These deprecation admonitions are not a plain "
            "`Warning: Deprecated`, so they were left alone. Please rewrite "
            "them as `Deprecated:` with no title, moving any extra wording "
            "into the body:\n" + _indented_list(report.ambiguous)
        )

    if report.unrendered:
        manual_step(
            "These symbols are deprecated by a helper, such as "
            "`deprecated_member()`, that warns at runtime but renders nothing "
            "in the documentation, and their docstring carries no "
            "`Deprecated:` admonition, so the rendered page never says they "
            "are deprecated. Please add one to each of these docstrings:\n"
            + _indented_list(report.unrendered)
        )

    if report.unmarked:
        manual_step(
            "These docstrings talk about a deprecation without carrying a "
            "`Deprecated:` admonition, so nothing marks it as one on the "
            "rendered page. The docstrings are searched for the word itself, "
            "case-insensitively, so expect false positives; please check each "
            "one and document the real deprecations:\n"
            + _indented_list(report.unmarked)
        )

    if report.duplicated or report.ambiguous or report.unrendered or report.unmarked:
        manual_step(
            "The deprecations guide explains how each of the deprecations "
            "listed above should be marked and documented:\n"
            f"      {_DEPRECATIONS_GUIDE_URL}"
        )


def _indented_list(locations: list[str]) -> str:
    """Indent the locations of a report so they read as a list.

    Args:
        locations: The locations to format.

    Returns:
        The locations, one per line, indented under the message.
    """
    return "\n".join(f"      {location}" for location in locations)


def _iter_python_files(root: Path) -> Iterator[Path]:
    """Yield the Python sources under ``root``, skipping build and tool output.

    Args:
        root: The directory to walk.

    Yields:
        Each Python source file found, in a stable order.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name
            for name in dirnames
            if not name.startswith(".")
            and name not in _SKIPPED_DIRS
            and not name.endswith(".egg-info")
        )
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            path = Path(dirpath, filename)
            if _THIS_SCRIPT is not None and path.resolve() == _THIS_SCRIPT:
                continue
            yield path


def _convert_deprecation_admonitions(  # pylint: disable=too-many-locals
    path: Path,
    content: str,
    tree: ast.Module,
    report: _DeprecationReport,
) -> tuple[str | None, int]:
    """Rewrite the `Warning: Deprecated` admonitions in one Python source.

    Args:
        path: The path of the source, only used to build report locations.
        content: The source as read from disk.
        tree: The parsed source.
        report: Collects everything found that a human has to deal with.

    Returns:
        The new source and the number of admonitions converted, or `None` and
        zero when nothing was converted.
    """
    lines = content.splitlines(keepends=True)
    converted = 0
    reported: set[int] = set()
    docstrings = _collect_docstrings(tree)

    for docstring in docstrings:
        # The summary is always the first line, so sections start on the next
        # one, and only the ones at the docstring's own indentation are
        # sections: anything deeper belongs to an `Args:` entry or similar.
        start = docstring.start
        last = min(docstring.end, len(lines))
        indents = [
            len(line) - len(line.lstrip()) for line in lines[start:last] if line.strip()
        ]
        if not indents:
            continue
        base_indent = min(indents)

        for index in range(start, last):
            match = _ADMONITION_RE.match(lines[index])
            if match is None:
                continue

            kind = match["kind"]
            title = match["title"].strip()
            indent = match["indent"]
            if len(indent) != base_indent:
                continue
            if kind != "Deprecated" and not _is_deprecation_title(title):
                continue
            if not _has_indented_body(lines, index, indent, docstring.end):
                continue

            location = f"{path}:{index + 1} ({docstring.name})"
            if docstring.decorated:
                report.duplicated.append(location)
                reported.add(index)
            elif kind == "Deprecated":
                if title:
                    report.ambiguous.append(
                        f"{location}: custom title `{kind}: {title}`"
                    )
                    reported.add(index)
            elif kind == "Warning" and title == "Deprecated":
                newline = lines[index][len(lines[index].rstrip("\r\n")) :]
                lines[index] = f"{indent}Deprecated:{newline}"
                converted += 1
            else:
                report.ambiguous.append(f"{location}: `{kind}: {title}`")
                reported.add(index)

    if not _is_test_code(path):
        headers, admonitions = _find_deprecated_admonitions(lines)
        report.unrendered.extend(
            _find_unrendered_deprecations(path, lines, docstrings, headers)
        )
        report.unmarked.extend(
            _find_unmarked_deprecations(path, lines, docstrings, reported | admonitions)
        )

    if converted == 0:
        return None, 0
    return "".join(lines), converted


def _is_test_code(path: Path) -> bool:
    """Tell whether a source holds tests rather than documented code.

    Every deprecation is supposed to be covered by a test asserting that it
    warns, so tests are where the word appears most and where it never means
    anything is missing.

    Args:
        path: The path of the source.

    Returns:
        Whether the source is a test.
    """
    return "tests" in path.parts or _TEST_FILE_RE.match(path.name) is not None


def _find_deprecated_admonitions(lines: list[str]) -> tuple[set[int], set[int]]:
    """Locate the `Deprecated:` admonitions already written in a source.

    Args:
        lines: The source lines.

    Returns:
        The indexes of the header lines, and the indexes of every line the
        admonitions occupy, header and body alike.
    """
    headers: set[int] = set()
    occupied: set[int] = set()

    # An admonition body is indented deeper than its header, so the block ends
    # at the first line that is not, which is also where the docstring ends.
    body_indent: int | None = None
    for index, line in enumerate(lines):
        if body_indent is not None:
            if not line.strip() or len(line) - len(line.lstrip()) > body_indent:
                occupied.add(index)
                continue
            body_indent = None
        header = _DEPRECATED_ADMONITION_RE.match(line)
        if header is not None:
            body_indent = len(header["indent"])
            headers.add(index)
            occupied.add(index)

    return headers, occupied


def _find_unrendered_deprecations(
    path: Path, lines: list[str], docstrings: list[_Docstring], headers: set[int]
) -> list[str]:
    """Find the symbols a helper deprecates without the documentation saying so.

    A helper such as `deprecated_member()` warns at runtime, but the griffe
    extension only renders the decorator, so the member's own docstring has to
    carry the admonition or the rendered page says nothing at all. A symbol
    whose docstring already has one is therefore not reported.

    Args:
        path: The path of the source, only used to build report locations.
        lines: The source lines, after the admonitions were converted.
        docstrings: The docstrings found in the source.
        headers: The indexes of the `Deprecated:` admonition headers.

    Returns:
        One `path:line (name)` location per symbol, in source order, cut short
        after `_MAX_MENTIONS_PER_FILE` of them.
    """
    found = sorted(
        (docstring.helper_line, f"{path}:{docstring.helper_line} ({docstring.name})")
        for docstring in docstrings
        if docstring.helper_line is not None
        and headers.isdisjoint(
            range(docstring.start - 1, min(docstring.end, len(lines)))
        )
    )
    return _cut_short(path, [location for _, location in found])


def _find_unmarked_deprecations(
    path: Path, lines: list[str], docstrings: list[_Docstring], excluded: set[int]
) -> list[str]:
    """Find the docstrings that talk about a deprecation without marking it.

    Most deprecations are announced as prose, in an `Args:` entry, an
    attribute docstring or a module summary, so the only way to find them all
    is to search for the word itself and let a human sort out the false
    positives.

    Only docstrings are searched. A deprecation has to be said in the
    documentation to reach the reader, and the word appears all over the code
    around one, in the `warnings.warn()` call that announces it at runtime and
    in every filter that silences it again, none of which is anything to fix.
    A `deprecated` decorator needs no exclusion either, since its message is
    not a docstring.

    Args:
        path: The path of the source, only used to build report locations.
        lines: The source lines, after the admonitions were converted.
        docstrings: The docstrings found in the source.
        excluded: The indexes of the lines already reported on their own, and
            of the admonitions that already render as written.

    Returns:
        One `path:line: text` location per mention left, in source order, cut
        short after `_MAX_MENTIONS_PER_FILE` of them.
    """
    candidates: set[int] = set()
    for docstring in docstrings:
        candidates.update(range(docstring.start - 1, min(docstring.end, len(lines))))
    candidates -= excluded

    return _cut_short(
        path,
        [
            f"{path}:{index + 1}: {lines[index].strip()}"
            for index in sorted(candidates)
            if _DEPRECATION_MENTION_RE.search(lines[index])
        ],
    )


def _cut_short(path: Path, found: list[str]) -> list[str]:
    """Keep a file's findings from burying the rest of the report.

    Args:
        path: The path the findings are in.
        found: The locations found in it.

    Returns:
        The locations, cut short after `_MAX_MENTIONS_PER_FILE` of them.
    """
    if len(found) <= _MAX_MENTIONS_PER_FILE:
        return found

    rest = len(found) - _MAX_MENTIONS_PER_FILE
    return found[:_MAX_MENTIONS_PER_FILE] + [f"{path}: ... and {rest} more"]


def _collect_docstrings(tree: ast.Module) -> list[_Docstring]:
    """Locate every docstring in a module, with the symbol that owns it.

    Attributes count too, through the string literal that follows their
    assignment: a module-level alias or an enum member is exactly the kind of
    symbol the decorator cannot reach, so the admonition is all it has.

    Args:
        tree: The parsed module.

    Returns:
        One `_Docstring` per docstring found, in no particular order.
    """
    found: list[_Docstring] = []

    def record(
        docstring: ast.Constant,
        name: str,
        *,
        decorated: bool = False,
        helper_line: int | None = None,
    ) -> None:
        found.append(
            _Docstring(
                start=docstring.lineno,
                end=docstring.end_lineno or docstring.lineno,
                name=name,
                decorated=decorated,
                helper_line=helper_line,
            )
        )

    module_docstring = _docstring_node(tree)
    if module_docstring is not None:
        record(module_docstring, "<module>")

    def walk(node: ast.AST, prefix: str) -> None:
        body = getattr(node, "body", None)
        if isinstance(body, list):
            for previous, statement in zip(body, body[1:]):
                target = _assignment_target(previous)
                attribute_docstring = _string_expression(statement)
                if target is not None and attribute_docstring is not None:
                    record(
                        attribute_docstring,
                        f"{prefix}.{target}" if prefix else target,
                        helper_line=_deprecation_helper_line(previous),
                    )

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified_name = f"{prefix}.{child.name}" if prefix else child.name
                docstring = _docstring_node(child)
                if docstring is not None:
                    record(
                        docstring,
                        qualified_name,
                        decorated=_has_deprecated_decorator(child),
                    )
                walk(child, qualified_name)
            elif hasattr(child, "body"):
                walk(child, prefix)

    walk(tree, "")
    return found


def _deprecation_helper_line(statement: ast.stmt) -> int | None:
    """Return the line where a helper deprecates the symbol a statement assigns.

    Args:
        statement: The assignment to inspect.

    Returns:
        The line of the call, or `None` when the statement assigns something
        else.
    """
    if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
        return None

    call = statement.value
    if not isinstance(call, ast.Call):
        return None

    if isinstance(call.func, ast.Attribute):
        name = call.func.attr
    elif isinstance(call.func, ast.Name):
        name = call.func.id
    else:
        return None

    return call.lineno if name in _DEPRECATION_HELPERS else None


def _docstring_node(node: ast.AST) -> ast.Constant | None:
    """Return the docstring literal of a node, if it has one.

    Args:
        node: The module, class or function to inspect.

    Returns:
        The string constant holding the docstring, or `None`.
    """
    body = getattr(node, "body", None)
    if not isinstance(body, list) or not body:
        return None
    return _string_expression(body[0])


def _string_expression(statement: ast.stmt) -> ast.Constant | None:
    """Return the string literal a statement consists of, if that is all it is.

    Args:
        statement: The statement to inspect.

    Returns:
        The string constant, or `None` when the statement is something else.
    """
    if (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    ):
        return statement.value
    return None


def _assignment_target(statement: ast.stmt) -> str | None:
    """Return the name a statement assigns to, if it assigns to just one.

    Args:
        statement: The statement to inspect.

    Returns:
        The name assigned to, or `None` when the statement is not a plain
        assignment to a single name.
    """
    if isinstance(statement, ast.Assign):
        targets = statement.targets
    elif isinstance(statement, ast.AnnAssign):
        targets = [statement.target]
    else:
        return None

    if len(targets) != 1 or not isinstance(targets[0], ast.Name):
        return None
    return targets[0].id


def _has_deprecated_decorator(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Tell whether a symbol carries a `deprecated` decorator.

    Any spelling counts: `@deprecated`, `@typing_extensions.deprecated` and
    `@warnings.deprecated`, called or not.

    Args:
        node: The class or function to inspect.

    Returns:
        Whether one of its decorators is named `deprecated`.
    """
    for decorator in node.decorator_list:
        expression = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(expression, ast.Attribute) and expression.attr == "deprecated":
            return True
        if isinstance(expression, ast.Name) and expression.id == "deprecated":
            return True
    return False


def _is_deprecation_title(title: str) -> bool:
    """Tell whether an admonition title announces a deprecation.

    Only the first word counts, so `Deprecated since v1.2` matches but
    `Deprecation-aware mode`, a section that merely talks about deprecations,
    does not.

    Args:
        title: The text after the admonition kind.

    Returns:
        Whether the title starts with a word announcing a deprecation.
    """
    words = title.split(maxsplit=1)
    if not words:
        return False
    return words[0].strip(".,;:!").lower() in ("deprecate", "deprecated", "deprecation")


def _has_indented_body(lines: list[str], index: int, indent: str, end: int) -> bool:
    """Tell whether a docstring section header is followed by its body.

    A `Title:` line only becomes an admonition when an indented block follows
    it; otherwise it is ordinary prose and must be left alone.

    Args:
        lines: The source lines.
        index: The index of the header line.
        indent: The indentation of the header line.
        end: The line number where the docstring ends.

    Returns:
        Whether the next non-blank line is indented deeper than the header.
    """
    for line in lines[index + 1 : end]:
        if not line.strip():
            continue
        return len(line) - len(line.lstrip()) > len(indent)
    return False


def manual_step(message: str) -> None:
    """Print a manual step message in yellow."""
    _manual_steps.append(message)
    print(f"\033[0;33m>>> {message}\033[0m")


if __name__ == "__main__":
    main()
