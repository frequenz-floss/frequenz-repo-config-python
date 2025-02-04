# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Integration between `mkdocstrings` and `macros` extensions to work together.

# Introduction

To be able to use macros inside docstrings, we need to integrate the
`mkdocs-macros` extension into `mkdocstrings`. This module provides the
necessary functions to make this integration work.

To use this module, add the following configuration to your `mkdocs.yml`:

```yaml title="mkdocs.yml"
plugins:
  # Order is important! mkdocstrings must come before macros!
  - mkdocstrings:
      default_handler: python
      # ...
  - macros:
      module_name: path/to/macros
      on_undefined: strict
      on_error_fail: true
```

Then you need to add the `path/to/macros.py` file. The contents will vary depending on
if you want to use use the convenience default hooking or not.

# Basic usage

A convenience [`define_env()`] function is provided to provide a [macros
extension](https://mkdocs-macros-plugin.readthedocs.io/en/latest/macros/) to do the
hooking and provide some useful variables and filters:

* [`slugify`][frequenz.repo.config.mkdocs.mkdocstrings_macros.slugify]: A filter to
    slugify a text. Useful to generate anchors for headings.
* [`code_annotation_marker`]: A variable to inject the appropriate HTML code for showing
    an example code annotation as a number (see
    [frequenz.repo.config.mkdocs.annotations][] for more information).

If you are happy with the defaults, your `path/to/macros.py` can look as simple as:

```py title="path/to/macros.py"
from frequenz.repo.config.mkdocs.mkdocstrings_macros import define_env
```

# Advanced usage

If you want to define your own macros, variables or filters, you'll need to provide your
own `define_env()` function, and call the hook to integrate with `mkdocstrings` at the
end.

Here is an example of how to do it:

```py title="path/to/macros.py"
from frequenz.repo.config.mkdocs.mkdocstrings_macros import hook_macros_plugin, slugify

def define_env(env: macros.MacrosPlugin) -> None:
    env.variables.my_var = "Example"
    env.filter(slugify, "slugify")

    # This hook needs to be done at the end of the `define_env` function.
    hook_macros_plugin(env)
```
"""


from typing import Any

import markdown as md
from markdown.extensions import toc
from mkdocs_macros import plugin as macros

from .annotations import CODE_ANNOTATION_MARKER


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
    def patched_update_env(md: md.Markdown, config: dict[str, Any]) -> None:
        update_env(md, config)

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
    env.variables.code_annotation_marker = CODE_ANNOTATION_MARKER
    env.filter(slugify, "slugify")  # type: ignore[no-untyped-call]

    # This hook needs to be done at the end of the `define_env` function.
    hook_macros_plugin(env)
