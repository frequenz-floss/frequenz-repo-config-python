# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""This module defines macros for use in Markdown files."""

import logging
from typing import Any

import markdown as md
from markdown.extensions import toc
from mkdocs_macros import plugin as macros

from frequenz.repo.config import github

_logger = logging.getLogger(__name__)

_CODE_ANNOTATION_MARKER: str = (
    r'<span class="md-annotation">'
    r'<span class="md-annotation__index" tabindex="-1">'
    r'<span data-md-annotation-id="1"></span>'
    r"</span>"
    r"</span>"
)


def _slugify(text: str) -> str:
    """Slugify a text.

    Args:
        text: The text to slugify.

    Returns:
        The slugified text.
    """
    # The type of the return value is not defined for the markdown library.
    # Also for some reason `mypy` thinks the `toc` module doesn't have a
    # `slugify_unicode` function, but it definitely does.
    return toc.slugify_unicode(text, "-")  # type: ignore[attr-defined,no-any-return]


def _add_version_variables(env: macros.MacrosPlugin) -> None:
    """Add variables with git information to the environment.

    Args:
        env: The environment to add the variables to.
    """
    env.variables["version"] = None
    env.variables["version_requirement"] = ""
    try:
        version_info = github.get_repo_version_info()
    except Exception as exc:  # pylint: disable=broad-except
        _logger.warning("Failed to get version info: %s", exc)
    else:
        env.variables["version"] = version_info
        if version_info.current_tag:
            env.variables["version_requirement"] = f" == {version_info.current_tag}"
        elif version_info.current_branch:
            env.variables["version_requirement"] = (
                " @ git+https://github.com/frequenz-floss/frequenz-repo-config-python"
                f"@{version_info.current_branch}"
            )


def _hook_macros_plugin(env: macros.MacrosPlugin) -> None:
    """Integrate the `mkdocs-macros` plugin into `mkdocstrings`.

    This is a temporary workaround to make `mkdocs-macros` work with
    `mkdocstrings` until a proper `mkdocs-macros` *pluglet* is available. See
    https://github.com/mkdocstrings/mkdocstrings/issues/615 for details.

    Args:
        env: The environment to hook the plugin into.
    """
    # get mkdocstrings' Python handler
    python_handler = env.conf["plugins"]["mkdocstrings"].get_handler("python")

    # get the `update_env` method of the Python handler
    update_env = python_handler.update_env

    # override the `update_env` method of the Python handler
    def patched_update_env(markdown: md.Markdown, config: dict[str, Any]) -> None:
        update_env(markdown, config)

        # get the `convert_markdown` filter of the env
        convert_markdown = python_handler.env.filters["convert_markdown"]

        # build a chimera made of macros+mkdocstrings
        def render_convert(markdown: str, *args: Any, **kwargs: Any) -> Any:
            return convert_markdown(env.render(markdown), *args, **kwargs)

        # patch the filter
        python_handler.env.filters["convert_markdown"] = render_convert

    # patch the method
    python_handler.update_env = patched_update_env


def define_env(env: macros.MacrosPlugin) -> None:
    """Define the hook to create macro functions for use in Markdown.

    Args:
        env: The environment to define the macro functions in.
    """
    # A variable to easily show an example code annotation from mkdocs-material.
    # https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#adding-annotations
    env.variables["code_annotation_marker"] = _CODE_ANNOTATION_MARKER

    _add_version_variables(env)

    # This hook needs to be done at the end of the `define_env` function.
    _hook_macros_plugin(env)
