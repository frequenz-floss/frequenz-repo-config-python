# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Cookiecutter pre-generation hooks.

This module contains the pre-generation hooks for the cookiecutter template. It
validates the cookiecutter variables and prints an error message and exits with a
non-zero exit code if any of them are invalid.
"""

import collections
import json
import re
import sys
from typing import Any

NAME_REGEX = re.compile(r"^[a-zA-Z][_a-zA-Z0-9]+(-[_a-zA-Z][_a-zA-Z0-9]+)*$")
PYTHON_PACKAGE_REGEX = re.compile(r"^[a-zA-Z][_a-zA-Z0-9]+(\.[_a-zA-Z][_a-zA-Z0-9]+)*$")
PYPI_PACKAGE_REGEX = NAME_REGEX


def to_named_tuple(dictionary: dict[Any, Any], /) -> Any:
    """Convert a dictionary to a named tuple.

    Args:
        dictionary: The dictionary to convert.

    Returns:
        The named tuple with the same keys and values as the dictionary.
    """
    filtered = {k: v for k, v in dictionary.items() if not k.startswith("_")}
    return collections.namedtuple("Cookiecutter", filtered.keys())(*filtered.values())


cookiecutter = to_named_tuple(json.loads(r"""{{cookiecutter | tojson}}"""))


def main() -> None:
    """Validate the cookiecutter variables.

    This function validates the cookiecutter variables and prints an error message and
    exits with a non-zero exit code if any of them are invalid.
    """
    errors: dict[str, list[str]] = {}

    def add_error(key: str, message: str) -> None:
        """Add an error to the error dictionary.

        Args:
            key: The key of the error.
            message: The error message.
        """
        errors.setdefault(key, []).append(message)

    if not NAME_REGEX.match(cookiecutter.name):
        add_error("name", f"Invalid project name (must match {NAME_REGEX.pattern})")

    if not PYTHON_PACKAGE_REGEX.match(cookiecutter.python_package):
        add_error(
            "python_package",
            f"Invalid package name (must match {PYTHON_PACKAGE_REGEX.pattern})",
        )

    if not PYPI_PACKAGE_REGEX.match(cookiecutter.pypi_package_name):
        add_error(
            "pypi_package_name",
            f"Invalid package name (must match {PYPI_PACKAGE_REGEX.pattern})",
        )

    if errors:
        print("The following errors were found:", file=sys.stderr)
        for key, messages in errors.items():
            print(f"  {key}:", file=sys.stderr)
            for message in messages:
                print(f"    - {message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
