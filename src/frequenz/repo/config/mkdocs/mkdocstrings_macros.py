# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Integration between `mkdocstrings` and `macros` extensions to work together.

# Introduction

To be able to use macros inside docstrings, we need to integrate the `mkdocs-macros`
extension into `mkdocstrings`. This module provides the necessary functions to make this
integration work.


# Basic usage

If you don't want to define your own macros, variables or filters, you can use this
module as a [pluglet](https://mkdocs-macros-plugin.readthedocs.io/en/latest/pluglets/):

```yaml title="mkdocs.yml"
plugins:
  # Order is important! mkdocstrings must come before macros!
  - mkdocstrings:
      default_handler: python
      # ...
  - macros:
      modules: ["frequenz.repo.config.mkdocs.mkdocstrings_macros"]
      on_undefined: strict
      on_error_fail: true
```

This will do the hooking and provide some useful variables and filters:

* [`slugify`][frequenz.repo.config.mkdocs.mkdocstrings_macros.slugify]: A filter to
    slugify a text. Useful to generate anchors for headings.
* [`code_annotation_marker`]: A variable to inject the appropriate HTML code for showing
    an example code annotation as a number (see
    [frequenz.repo.config.mkdocs.annotations][] for more information).
* [`version`]: A varaible with the version information of the repository as exposed by
    [`get_repo_version_info()`][frequenz.repo.config.github.get_repo_version_info],
    which means some environment variables are required (this variable will be `None`
    otherwise), please read the function documentation for more details.
* [`version_requirement`]: A variable with the version requirement for the current
    version of the repository. It is built using the information from `version`. Also
    only available if the rigth environment variables are set, and if the resulting
    version is a tag (will be empty for branches). If you want to get the version
    requirement for a branch, you need to provide a `repo_url` variable in the
    `mkdocs.yaml` file or do a custom setup. Please read the [Customized usage]
    section for more details.


# Customized usage

If you want to define your own macros, variables or filters, but you also want to get
the default behaviour described in [Basic usage], you need to provide your own [macros
module](https://mkdocs-macros-plugin.readthedocs.io/en/latest/macros/) with
a `define_env()` function. You can specify it in the `mkdocs.yml` configuration file:

```yaml title="mkdocs.yml"
plugins:
  # Order is important! mkdocstrings must come before macros!
  - mkdocstrings:
      default_handler: python
      # ...
  - macros:
      module_name: "path/to/macros" # Note: no .py extension here!
      on_undefined: strict
      on_error_fail: true
```

Then you need to add the `define_env()` function to the `path/to/macros.py` file.
A convenience [`hook_env_with_everything()`] is provided to pull all the same default
variables and filters and call the hooking function at the end as with the *pluglet*.

You also need to make sure to call the function at the end, after you define your own
variables, filters and macros. You can optionally pass a `repo_url` in this case so the
`version_requirement` variable can work when the current version is a branch. If a
`repo_url` variable is present in the `mkdocs.yml` file, it will be used as the default.

Here is an example of how to do it:

```py title="path/to/macros.py"
from frequenz.repo.config.mkdocs.mkdocstrings_macros import hook_env_with_everything

def define_env(env: macros.MacrosPlugin) -> None:
    env.variables.my_var = "Example"

    # This hook needs to be done at the end of the `define_env` function.
    hook_env_with_everything(env, "https://your-repo-url")
```

# Advanced usage

If you don't want to pull in all the default variables and filters, you can still define
your own `define_env()` function and do the same configuration in the `mkdocs.yml` file
as in the [Customized usage] section, but instead call the
[`hook_macros_plugin()`][frequenz.repo.config.mkdocs.mkdocstrings_macros.hook_macros_plugin]
at the end.

Here is an example of how to do it:

```py title="path/to/macros.py"
from frequenz.repo.config.mkdocs.mkdocstrings_macros import hook_macros_plugin

def define_env(env: macros.MacrosPlugin) -> None:
    env.variables.my_var = "Example"

    # This hook needs to be done at the end of the `define_env` function.
    hook_macros_plugin(env)
```
"""


import logging
from typing import Any

from markdown.extensions import toc
from mkdocs_macros import plugin as macros

from ..github import get_repo_version_info
from .annotations import CODE_ANNOTATION_MARKER

_logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Slugify a text.

    Useful to generate anchors for headings.

    Example:
        ```markdown
        Some URL: https://example.com/#{{ "My Heading" | slugify }}.
        ```

    Args:
        text: The text to slugify.

    Returns:
        The slugified text.
    """
    return toc.slugify_unicode(text, "-")


def add_version_variables(
    env: macros.MacrosPlugin, *, repo_url: str | None = None
) -> None:
    """Add variables with git information to the environment.

    This function will add 2 new macro variables to `env`:

    * [`version`]: A varaible with the version information of the repository as exposed by
        [`get_repo_version_info()`][frequenz.repo.config.github.get_repo_version_info],
        which means some environment variables are required (this variable will be `None`
        otherwise), please read the function documentation for more details.
    * [`version_requirement`]: A variable with the version requirement for the current
        version of the repository. It is built using the information from `version`. Also
        only available if the rigth environment variables are set, and if the resulting
        version is a tag (will be empty for branches). If you want to get the version
        requirement for a branch, you need to provide a `repo_url` or a `repo_url`
        config in the `mkdocs.yml` file.

    Args:
        env: The environment to add the variables to.
        repo_url: The URL of the repository to use in the `version_requirement`
            variable. If `None` the `config.repo_url` mkdocs variable will be used. Only
            needed if you want to use the `version_requirement` variable for branches.
    """
    env.variables["version"] = None
    env.variables["version_requirement"] = ""

    if repo_url is None:
        repo_url = env.variables.get("config", {}).get("repo_url")
        if repo_url is None:
            _logger.warning(
                "No repo_url provided, can't build the 'version_requirement' variable"
            )

    version_info = None
    try:
        version_info = get_repo_version_info()
    except Exception as exc:  # pylint: disable=broad-except
        _logger.warning("Failed to get version info: %s", exc)
    else:
        env.variables["version"] = version_info
        if version_info.current_tag:
            env.variables["version_requirement"] = f" == {version_info.current_tag}"

    ref = None
    if version_info is not None:
        ref = version_info.current_branch or version_info.sha
    ref = ref or env.variables.get("git", {}).get("commit")
    if ref and repo_url is not None:
        env.variables["version_requirement"] = f" @ git+{repo_url}@{ref}"


def hook_macros_plugin(env: macros.MacrosPlugin) -> None:
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
    def patched_update_env(config: dict[str, Any]) -> None:
        update_env(config=config)

        # get the `convert_markdown` filter of the env
        convert_markdown = python_handler.env.filters["convert_markdown"]

        # build a chimera made of macros+mkdocstrings
        def render_convert(markdown: str, *args: Any, **kwargs: Any) -> Any:
            return convert_markdown(env.render(markdown), *args, **kwargs)

        # patch the filter
        python_handler.env.filters["convert_markdown"] = render_convert

    # patch the method
    python_handler.update_env = patched_update_env


def hook_env_with_everything(
    env: macros.MacrosPlugin, *, repo_url: str | None = None
) -> None:
    """Hooks the `env` with all the default variables and filters.

    This function is a convenience function that adds all variables and filters and
    macros provided by this module and calls
    [`hook_macros_plugin()`][frequenz.repo.config.mkdocs.mkdocstrings_macros.hook_macros_plugin]
    at the end.

    Args:
        env: The environment to hook.
        repo_url: The URL of the repository to use in the `version_requirement`
            variable. If `None` the `config.repo_url` mkdocs variable will be used. Only
            needed if you want to use the `version_requirement` variable for branches.
    """
    env.variables.code_annotation_marker = CODE_ANNOTATION_MARKER
    add_version_variables(env, repo_url=repo_url)

    env.filter(slugify, "slugify")  # type: ignore[no-untyped-call]

    # This hook needs to be done at the end of the `define_env` function.
    hook_macros_plugin(env)


def define_env(env: macros.MacrosPlugin) -> None:
    """Define the hook to create macro functions for use in Markdown.

    Args:
        env: The environment to define the macro functions in.
    """
    hook_env_with_everything(env)
