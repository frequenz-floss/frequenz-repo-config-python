# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Setuptool hooks to build protobuf files."""

from __future__ import annotations

import pathlib
import subprocess
import sys
from collections.abc import Iterable
from typing import Any

import setuptools
import setuptools.command.build_py


def build_proto_cmdclass(
    *,
    proto_path: str = "proto",
    proto_glob: str = "*.proto",
    include_paths: Iterable[str] = ("submodules/api-common-protos",),
) -> dict[str, Any]:
    """Return a dictionary with the required machinery to build protobuf files.

    Args:
        proto_path: Path of the root directory containing the protobuf files.
        proto_glob: The glob pattern to use to find the protobuf files.
        include_paths: Paths to include when compiling the protobuf files.

    Returns:
        Options to pass to `setuptools.setup()` `cmdclass` argument to build
        protobuf files.

    Examples:
        To use this you need to make sure you have these dependencies:

        * `grpcio-tools >= 1.47.0, < 2`
        * `mypy-protobuf >= 3.0.0, < 4`

        TODO: SUBMODULE

        ```py
        import setuptools

        if __name__ == "__main__":
            setuptools.setup(cmdclass=build_proto_cmdclass())
        ```
    """

    class CompileProto(setuptools.Command):
        """Command class to build the Python protobuf files."""

        description: str = f"compile protobuf files in {proto_path}/**/{proto_glob}/"
        user_options: list[str] = []

        def initialize_options(self) -> None:
            """Initialize options."""

        def finalize_options(self) -> None:
            """Finalize options."""

        def run(self) -> None:
            """Compile the Python protobuf files."""
            proto_files = [str(p) for p in pathlib.Path(proto_path).rglob(proto_glob)]
            protoc_cmd = (
                [sys.executable, "-m", "grpc_tools.protoc"]
                + [f"-I{p}" for p in [*include_paths, proto_path]]
                + """--python_out=py
                    --grpc_python_out=py
                    --mypy_out=py
                    --mypy_grpc_out=py
                    """.split()
                + proto_files
            )
            print(f"Compiling proto files via: {' '.join(protoc_cmd)}")
            subprocess.run(protoc_cmd, check=True)

    class BuildPy(setuptools.command.build_py.build_py, CompileProto):
        """Command class to build the Python protobuf files."""

        def run(self) -> None:
            """Compile the Python protobuf files and run regular `build_py`."""
            CompileProto.run(self)
            setuptools.command.build_py.build_py.run(self)

    return {
        "compile_proto": CompileProto,
        # Compile the proto files to python files. This is done when building
        # the wheel, the source distribution (sdist) contains the *.proto files
        # only. Check the MANIFEST.in file to see which files are included in
        # the sdist, and the tool.setuptools.package-dir,
        # tool.setuptools.package-data, and tools.setuptools.packages
        # configuration keys in pyproject.toml to see which files are included
        # in the wheel package.
        "build_py": BuildPy,
    }
