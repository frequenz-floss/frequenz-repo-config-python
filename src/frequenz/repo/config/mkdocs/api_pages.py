# License: MIT
# Copyright © 2022 Frequenz Energy-as-a-Service GmbH

"""Generate the code reference pages.

It uses the following `mkdocs` plugins:

* `mkdocs-gen-files` to generate the API documentation pages.
* `mkdocs-literate-nav` to make use of the generate `SUMMARY.md` file.

Based on the recipe at:
https://mkdocstrings.github.io/recipes/#automatic-code-reference-pages
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

import mkdocs_gen_files

from .. import protobuf as _protobuf


def _is_internal(path_parts: Tuple[str, ...]) -> bool:
    """Tell if the path is internal judging by the parts.

    Args:
        path_parts: Path.parts of the path to check.

    Returns:
        True if the path is internal.
    """

    def with_underscore_not_init(part: str) -> bool:
        return part.startswith("_") and part != "__init__"

    is_conftest = path_parts[-1] == "conftest" if path_parts else False

    return is_conftest or any(p for p in path_parts if with_underscore_not_init(p))


def generate_python_api_pages(
    src_path: str = "src", dst_path: str = "python-reference"
) -> None:
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


def generate_protobuf_api_pages(
    src_path: str = "proto", dst_path: str = "protobuf-reference"
) -> None:
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
    config = _protobuf.ProtobufConfig.from_pyproject_toml(
        proto_path=src_path, docs_path=dst_path
    )

    cwd = Path.cwd()

    with tempfile.TemporaryDirectory(prefix="mkdocs-protobuf-reference-") as tmp_path:
        for path in sorted(Path(config.proto_path).rglob("*.proto")):
            doc_path = path.relative_to(config.proto_path).with_suffix(".md")
            full_doc_path = Path(config.docs_path, doc_path)
            parts = tuple(path.relative_to(config.proto_path).parts)
            nav[parts] = doc_path.as_posix()
            doc_tmp_path = tmp_path / doc_path
            doc_tmp_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(
                    [
                        "docker",
                        "run",
                        "--rm",
                        f"-v{cwd}:{cwd}",
                        f"-v{tmp_path}:{tmp_path}",
                        "pseudomuto/protoc-gen-doc",
                        f"-I{cwd / config.proto_path}",
                        *(f"-I{cwd / p}" for p in config.include_paths),
                        f"--doc_opt=markdown,{doc_path.name}",
                        f"--doc_out={tmp_path / doc_path.parent}",
                        str(cwd / path),
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as error:
                print(f"Error generating protobuf reference page: {error}")

            with doc_tmp_path.open() as input_file, mkdocs_gen_files.open(
                full_doc_path, "w"
            ) as output_file:
                output_file.write(input_file.read())

            mkdocs_gen_files.set_edit_path(full_doc_path, Path("..") / path)

    with mkdocs_gen_files.open(Path(config.docs_path) / "SUMMARY.md", "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())
