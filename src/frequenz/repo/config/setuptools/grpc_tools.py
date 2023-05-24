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
import tomllib as _tomllib

import setuptools as _setuptools

# The typing stub for this module is missing
import setuptools.command.build as _build_command  # type: ignore[import]


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

    DEFAULT_OPTIONS: dict[str, str] = {
        "proto_path": "proto",
        "proto_glob": "*.proto",
        "include_paths": "submodules/api-common-protos,submodules/frequenz-api-common/proto",
        "py_path": "py",
    }

    def initialize_options(self) -> None:
        """Initialize options."""
        options = self._get_options_from_pyproject_toml(self.DEFAULT_OPTIONS)

        self.proto_path = options["proto_path"]
        self.proto_glob = options["proto_glob"]
        self.include_paths = options["include_paths"]
        self.py_path = options["py_path"]

    def finalize_options(self) -> None:
        """Finalize options."""

    def _get_options_from_pyproject_toml(
        self, defaults: dict[str, str]
    ) -> dict[str, str]:
        """Get the options from the pyproject.toml file.

        The options are read from the `[tool.frequenz-repo-config.setuptools.grpc_tools]`
        section of the pyproject.toml file.

        Args:
            defaults: The default values for the options.

        Returns:
            The options read from the pyproject.toml file.
        """
        try:
            with _pathlib.Path("pyproject.toml").open("rb") as toml_file:
                pyproject_toml = _tomllib.load(toml_file)
        except FileNotFoundError:
            return defaults
        except (IOError, OSError) as err:
            print(f"WARNING: Failed to load pyproject.toml: {err}")
            return defaults

        try:
            config = pyproject_toml["tool"]["frequenz-repo-config"]["setuptools"][
                "grpc_tools"
            ]
        except KeyError:
            return defaults

        known_keys = frozenset(defaults.keys())
        config_keys = frozenset(config.keys())
        if unknown_keys := config_keys - known_keys:
            print(
                "WARNING: There are some configuration keys in pyproject.toml we don't "
                "know about and will be ignored: "
                + ", ".join(f"'{k}'" for k in unknown_keys)
            )

        if "include_paths" in config:
            config["include_paths"] = ",".join(config["include_paths"])

        return dict(defaults, **{k: config[k] for k in (known_keys & config_keys)})

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
