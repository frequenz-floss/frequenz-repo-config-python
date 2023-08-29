# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Setuptool hooks to build protobuf files.

This module contains a setuptools command that can be used to compile protocol
buffer files in a project.

It also runs the command as the first sub-command for the build command, so
protocol buffer files are compiled automatically before the project is built.
"""

import pathlib as _pathlib
import subprocess as _subprocess
import sys as _sys

import setuptools as _setuptools
import setuptools.command.build as _build_command

from .. import protobuf as _protobuf


class CompileProto(_setuptools.Command):
    """Build the Python protobuf files."""

    proto_path: str
    """The path of the root directory containing the protobuf files."""

    proto_glob: str
    """The glob pattern to use to find the protobuf files."""

    include_paths: str
    """Comma-separated list of paths to include when compiling the protobuf files."""

    py_path: str
    """The path of the root directory where the Python files will be generated."""

    description: str = "compile protobuf files"
    """Description of the command."""

    user_options: list[tuple[str, str | None, str]] = [
        (
            "proto-path=",
            None,
            "path of the root directory containing the protobuf files",
        ),
        ("proto-glob=", None, "glob pattern to use to find the protobuf files"),
        (
            "include-paths=",
            None,
            "comma-separated list of paths to include when compiling the protobuf files",
        ),
        (
            "py-path=",
            None,
            "path of the root directory where the Python files will be generated",
        ),
    ]
    """Options of the command."""

    def initialize_options(self) -> None:
        """Initialize options."""
        config = _protobuf.ProtobufConfig.from_pyproject_toml()

        self.proto_path = config.proto_path
        self.proto_glob = config.proto_glob
        self.include_paths = ",".join(config.include_paths)
        self.py_path = config.py_path

    def finalize_options(self) -> None:
        """Finalize options."""

    def run(self) -> None:
        """Compile the Python protobuf files."""
        include_paths = self.include_paths.split(",")
        proto_files = [
            str(p) for p in _pathlib.Path(self.proto_path).rglob(self.proto_glob)
        ]

        if not proto_files:
            print(
                f"No proto files found in {self.proto_path}/**/{self.proto_glob}/, "
                "skipping compilation of proto files."
            )
            return

        protoc_cmd = (
            [_sys.executable, "-m", "grpc_tools.protoc"]
            + [f"-I{p}" for p in [*include_paths, self.proto_path]]
            + [
                f"--{opt}={self.py_path}"
                for opt in "python_out grpc_python_out mypy_out mypy_grpc_out".split()
            ]
            + proto_files
        )

        print(f"Compiling proto files via: {' '.join(protoc_cmd)}")
        _subprocess.run(protoc_cmd, check=True)


# This adds the compile_proto command to the build sub-command.
# The name of the command is mapped to the class name in the pyproject.toml file,
# in the [project.entry-points.distutils.commands] section.
# The None value is an optional function that can be used to determine if the
# sub-command should be executed or not.
_build_command.build.sub_commands.insert(0, ("compile_proto", None))
