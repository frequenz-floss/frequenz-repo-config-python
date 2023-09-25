# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Local cookiecutter extensions.

This module contains local cookiecutter extensions that are useful for generating the
project structure.
"""

import json as _json
import pathlib as _pathlib

from jinja2 import Environment as _Environment
from jinja2.ext import Extension as _Extension
from jinja2.nodes import Node as _Node
from jinja2.parser import Parser as _Parser


class RepoConfigExtension(_Extension):
    """Extension to add variables and filters to the cookiecutter context.

    Every method starting and ending with `_FILTER_PREFIX` and `_FILTER_SUFFIX`
    respectively will be registered as a filter. The name of the filter will be the
    method name without the prefix and suffix.
    """

    _FILTER_PREFIX = "_"
    _FILTER_SUFFIX = "_filter"

    def __init__(self, environment: _Environment):
        """Initialize this extension.

        Args:
            environment: The Jinja2 environment.
        """
        super().__init__(environment)
        self._register_filters()

    def parse(self, parser: _Parser) -> _Node | list[_Node]:
        """Parse tags declared by this extension.

        This is a NOP because we don't declare any tags, but we need to implement this
        methods because it's abstract in the base class.

        Args:
            parser: The Jinja2 parser.

        Returns:
            An empty list.
        """
        return []

    def _register_filters(self) -> None:
        """Register all filters in this extension with the Jinja2 environment."""
        filters = [
            name[len(self._FILTER_PREFIX) : -len(self._FILTER_SUFFIX)]
            for name in dir(self)
            if name.startswith(self._FILTER_PREFIX)
            and name.endswith(self._FILTER_SUFFIX)
        ]
        for filer_name in filters:
            attr_name = f"{self._FILTER_PREFIX}{filer_name}{self._FILTER_SUFFIX}"
            self.environment.filters[filer_name] = getattr(self, attr_name)

    def _build_identifier(self, repo_type: str, name: str, separator: str) -> str:
        """Build an identifier depending on the repository type.

        Args:
            repo_type: The repository type.
            name: The project name.
            separator: The separator to use to construct the identifier.

        Returns:
            The built identifier.
        """
        if separator == ".":
            name = name.replace("-", "_")
        if separator == "-":
            name = name.replace("_", "-")
        name = name.lower()
        middle = f"{repo_type}{separator}" if repo_type != "lib" else ""
        return f"frequenz{separator}{middle}{name}"

    def _get_from_json(self, key: str) -> str:
        """Get a string from the cookiecutter.json file.

        Args:
            key: The key to get the string for.

        Returns:
            The string from the cookiecutter.json file.
        """
        with open("../cookiecutter.json", encoding="utf8") as cookiecutter_json_file:
            return str(_json.load(cookiecutter_json_file)[key])

    def _as_identifier_filter(self, name: str) -> str:
        """Convert a name to a valid identifier.

        Args:
            name: The name to convert.

        Returns:
            The converted identifier.
        """
        return name.lower().replace("-", "_")

    def _python_package_filter(self, cookiecutter: dict[str, str]) -> str:
        """Generate the Python package (import) depending on the repository type.

        Args:
            cookiecutter: The cookiecutter context.

        Returns:
            The Python package name that can be used in import statements.
        """
        return self._build_identifier(cookiecutter["type"], cookiecutter["name"], ".")

    def _pypi_package_name_filter(self, cookiecutter: dict[str, str]) -> str:
        """Generate the PyPI package name depending on the repository type.

        Args:
            cookiecutter: The cookiecutter context.

        Returns:
            The PyPI package name depending on the repository type.
        """
        return self._build_identifier(cookiecutter["type"], cookiecutter["name"], "-")

    def _github_repo_name_filter(self, cookiecutter: dict[str, str]) -> str:
        """Generate the Python package name depending on the repository type.

        Args:
            cookiecutter: The cookiecutter context.

        Returns:
            The Python package name depending on the repository type.
        """
        pypi = self._build_identifier(cookiecutter["type"], cookiecutter["name"], "-")
        end = "-python" if cookiecutter["type"] == "lib" else ""
        return f"{pypi}{end}"

    def _title_filter(self, cookiecutter: dict[str, str]) -> str:
        """Build a default mkdocs site name for the project.

        Args:
            cookiecutter: The cookiecutter context.

        Returns:
            The default site name.
        """
        name = cookiecutter["name"].replace("_", " ").replace("-", " ").title()
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

    def _src_path_filter(self, cookiecutter: dict[str, str]) -> str:
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

    def _keywords_filter(self, cookiecutter: dict[str, str]) -> str:
        """Extend cookiecutter["keywords"] with predefined ones by repository type.

        Args:
            cookiecutter: The cookiecutter context.

        Returns:
            The extended keywords.
        """
        repo_type = cookiecutter["type"]
        extended_keywords = ["frequenz", "python", repo_type]
        match repo_type:
            case "api":
                extended_keywords.extend(["grpc", "protobuf", "rpc"])
            case "app":
                extended_keywords.extend(["application"])
            case "lib":
                extended_keywords.extend(["library"])
            case "model":
                extended_keywords.extend(["ai", "ml", "machine-learning"])
        extended_keywords.append(cookiecutter["name"])
        default = self._get_from_json("keywords")
        cookiecutter_keywords = cookiecutter["keywords"]
        if cookiecutter_keywords == default:
            cookiecutter_keywords = ""
        extended_keywords.extend(
            k.strip() for k in cookiecutter_keywords.split(",") if k
        )
        return _json.dumps(extended_keywords)

    def _default_codeowners_filter(self, cookiecutter: dict[str, str]) -> str:
        """Build a default description for the project.

        Args:
            cookiecutter: The cookiecutter context.

        Returns:
            The default description.
        """
        repo_type = cookiecutter["type"]

        codeowners = cookiecutter["default_codeowners"]
        default = self._get_from_json("default_codeowners")
        if codeowners != default:
            return codeowners

        github_org = self._get_from_json("github_org")
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

    def _introduction_filter(
        self, cookiecutter: dict[str, str]  # pylint: disable=unused-argument
    ) -> str:
        """Build an introduction text for the project generation.

        Args:
            cookiecutter: The cookiecutter context.

        Returns:
            The introduction text.
        """
        with (
            _pathlib.Path(__file__).parent / "variable-reference.md"
        ).open() as doc_file:
            variable_reference = doc_file.read()
        return f"""]

    Welcome to repo-config Cookiecutter template!

    This template will help you to create a new repository for your project. \
    You will be asked to provide some information about your project.

    Here is an explanation of what each variable is for and will be used for:

    {variable_reference}

    [Please press any key to continue"""
