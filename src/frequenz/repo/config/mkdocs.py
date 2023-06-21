# License: MIT
# Copyright © 2022 Frequenz Energy-as-a-Service GmbH

"""Generate the code reference pages.

It uses the following `mkdocs` plugins:

* `mkdocs-gen-files` to generate the API documentation pages.
* `mkdocs-literate-nav` to make use of the generate `SUMMARY.md` file.

Based on the recipe at:
https://mkdocstrings.github.io/recipes/#automatic-code-reference-pages
"""

from pathlib import Path
from typing import Tuple

import mkdocs_gen_files


def _is_internal(path_parts: Tuple[str, ...]) -> bool:
    """Tell if the path is internal judging by the parts.

    Args:
        path_parts: Path.parts of the path to check.

    Returns:
        True if the path is internal.
    """

    def with_underscore_not_init(part: str) -> bool:
        return part.startswith("_") and part != "__init__"

    return any(p for p in path_parts if with_underscore_not_init(p))


def generate_api_pages(src_path: str = "src", dst_path: str = "reference") -> None:
    """Generate API documentation pages for the code.

    Internal modules (those starting with an underscore except from `__init__`) are
    not included.

    A summary page is generated as `SUMMARY.md` which is compatible with the
    `mkdocs-literary-nav` plugin.

    Args:
        src_path: Path where the code is located.
        dst_path: Path where the documentation should be generated.  This is relative
            to the output directory of mkdocs.
    """
    # type ignore because mkdocs_gen_files uses a very weird module-level
    # __getattr__() which messes up the type system
    nav = mkdocs_gen_files.Nav()  # type: ignore

    for path in sorted(Path(src_path).rglob("*.py")):
        module_path = path.relative_to(src_path).with_suffix("")

        doc_path = path.relative_to(src_path).with_suffix(".md")
        full_doc_path = Path(dst_path, doc_path)
        parts = tuple(module_path.parts)
        if _is_internal(parts):
            continue
        if parts[-1] == "__init__":
            doc_path = doc_path.with_name("index.md")
            full_doc_path = full_doc_path.with_name("index.md")
            parts = parts[:-1]

        nav[parts] = doc_path.as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as output_file:
            output_file.write(f"::: {'.'.join(parts)}\n")

        mkdocs_gen_files.set_edit_path(full_doc_path, Path("..") / path)

    with mkdocs_gen_files.open(Path(dst_path) / "SUMMARY.md", "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())
