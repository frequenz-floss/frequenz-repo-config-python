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


def _get_from_json(key: str) -> str:
    """Get a string from the cookiecutter.json file.

    Args:
        key: The key to get the string for.

    Returns:
        The string from the cookiecutter.json file.
    """
    with open("../cookiecutter.json", encoding="utf8") as cookiecutter_json_file:
        return str(_json.load(cookiecutter_json_file)[key])


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
def title(cookiecutter: dict[str, str]) -> str:
    """Build a default mkdocs site name for the project.

    Args:
        cookiecutter: The cookiecutter context.

    Returns:
        The default site name.
    """
    name = cookiecutter["name"].capitalize()
    match cookiecutter["type"]:
        case "actor":
            return f"Frequenz {name} Actor"
        case "api":
            return f"Frequenz {name} API"
        case "lib":
            return f"Freqenz {name} Library"
        case "app":
            return f"Frequenz {name} Application"
        case "model":
            return f"Frequenz {name} AI Model"
        case _ as repo_type:
            assert False, f"Unhandled repository type {repo_type!r}"


@_simple_filter  # type: ignore[misc]
def src_path(cookiecutter: dict[str, str]) -> str:
    """Build a default source path for the project.

    Args:
        cookiecutter: The cookiecutter context.

    Returns:
        The default source path.
    """
    match cookiecutter["type"]:
        case "api":
            return "py"
        case "actor" | "lib" | "app" | "model":
            return "src"
        case _ as repo_type:
            assert False, f"Unhandled repository type {repo_type!r}"


@_simple_filter  # type: ignore[misc]
def keywords(cookiecutter: dict[str, str]) -> str:
    """Extend cookiecutter["keywords"] with predefined ones by repository type.

    Args:
        cookiecutter: The cookiecutter context.

    Returns:
        The extended keywords.
    """
    repo_type = cookiecutter["type"]
    extended_keywords = ["frequenz", "python", repo_type]
    if repo_type == "api":
        extended_keywords.extend(["grpc", "protobuf", "rpc"])
    extended_keywords.append(cookiecutter["name"])
    default = _get_from_json("keywords")
    cookiecutter_keywords = cookiecutter["keywords"]
    if cookiecutter_keywords == default:
        cookiecutter_keywords = ""
    extended_keywords.extend(k.strip() for k in cookiecutter_keywords.split(","))
    return _json.dumps(extended_keywords)


@_simple_filter  # type: ignore[misc]
def default_codeowners(cookiecutter: dict[str, str]) -> str:
    """Build a default description for the project.

    Args:
        cookiecutter: The cookiecutter context.

    Returns:
        The default description.
    """
    repo_type = cookiecutter["type"]

    codeowners = cookiecutter["default_codeowners"]
    default = _get_from_json("default_codeowners")
    if codeowners != default:
        return codeowners

    github_org = _get_from_json("github_org")
    if github_org != "frequenz-floss":
        return f"TODO(cookiecutter): Add codeowners (like @{github_org}/some-team)"

    type_to_team = {
        "actor": "TODO(cookiecutter): Add codeowners (like @{github_org}/some-team)"
        "# Temporary, should probably change",
        "api": "@frequenz-floss/api-team",
        "lib": "@frequenz-floss/python-sdk-team",
        "app": "@frequenz-floss/python-sdk-team @frequenz-floss/datasci-team "
        "# Temporary, should probably change",
        "model": "@frequenz-floss/datasci-team",
    }

    assert repo_type in type_to_team, f"Unhandled repository type {repo_type!r}"

    return type_to_team[repo_type]
