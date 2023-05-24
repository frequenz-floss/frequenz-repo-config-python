# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Local cookiecutter extensions.

This module contains local cookiecutter extensions that are useful for generating the
project structure.
"""

import json as _json

from cookiecutter.utils import simple_filter as _simple_filter


def _build_identifier(repo_type: str, name: str, separator: str) -> str:
    """Build an identifier depending on the repository type.

    Args:
        repo_type: The repository type.
        name: The project name.
        separator: The separator to use to construct the identifier.

    Returns:
        The built identifier.
    """
    middle = f"{repo_type}{separator}" if repo_type != "lib" else ""
    return f"frequenz{separator}{middle}{name}"


# Ignoring because cookiecutter simple_filter decorator is not typed.
@_simple_filter  # type: ignore[misc]
def python_package(cookiecutter: dict[str, str]) -> str:
    """Generate the Python package (import) depending on the repository type.

    Args:
        cookiecutter: The cookiecutter context.

    Returns:
        The Python package name that can be used in import statements.
    """
    return _build_identifier(cookiecutter["type"], cookiecutter["name"], ".")


@_simple_filter  # type: ignore[misc]
def pypi_package_name(cookiecutter: dict[str, str]) -> str:
    """Generate the PyPI package name depending on the repository type.

    Args:
        cookiecutter: The cookiecutter context.

    Returns:
        The PyPI package name depending on the repository type.
    """
    return _build_identifier(cookiecutter["type"], cookiecutter["name"], "-")


@_simple_filter  # type: ignore[misc]
def github_repo_name(cookiecutter: dict[str, str]) -> str:
    """Generate the Python package name depending on the repository type.

    Args:
        cookiecutter: The cookiecutter context.

    Returns:
        The Python package name depending on the repository type.
    """
    pypi = _build_identifier(cookiecutter["type"], cookiecutter["name"], "-")
    end = "-python" if cookiecutter["type"] == "lib" else ""
    return f"{pypi}{end}"


@_simple_filter  # type: ignore[misc]
def keywords(cookiecutter: dict[str, str]) -> str:
    """Extend cookiecutter["keywords"] with predefined ones by repository type.

    Args:
        cookiecutter: The cookiecutter context.

    Returns:
        The extended keywords.
    """
    repo_type = cookiecutter["type"]
    extended_keywords = ["frequenz", repo_type]
    if repo_type == "api":
        extended_keywords.append("grpc")
    extended_keywords.append(cookiecutter["name"])
    with open("../cookiecutter.json", encoding="utf8") as cookiecutter_json_file:
        no_input = _json.load(cookiecutter_json_file)["keywords"]
    cookiecutter_keywords = cookiecutter["keywords"]
    if cookiecutter_keywords == no_input:
        cookiecutter_keywords = ""
    extended_keywords.extend(k.strip() for k in cookiecutter_keywords.split(","))
    return _json.dumps(extended_keywords)
