# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Default nox configuration for different types of repositories.

This module provides the default configuration for the different types of
repositories defined by
[`RepositoryType`][...RepositoryType].

The [`actor_config`][.actor_config], [`api_config`][.api_config],
[`app_config`][.app_config], [`lib_config`][.lib_config], and
[`model_config`][.model_config] variables are the default configurations for actors,
APIs, applications, libraries, and models, respectively. The
[`common_config`][.common_config] variable is the default configuration for all types of
repositories.

The [`actor_command_options`][.actor_command_options],
[`api_command_options`][.api_command_options], [`app_command_options`][.app_command_options],
[`lib_command_options`][.lib_command_options], and
[`model_command_options`][.model_command_options] variables are the default
command-line options for the same types of repositories, and the
[`common_command_options`][.common_command_options] variable is the default command-line
options for all types of repositories.

They can be modified before being passed to
[`nox.configure()`][..configure] by using the
[`CommandsOptions.copy()`][..config.CommandsOptions.copy]
method.
"""

from . import config as _config

common_command_options: _config.CommandsOptions = _config.CommandsOptions(
    black=[
        "--check",
    ],
    flake8=[],
    isort=[
        "--diff",
        "--check",
    ],
    mypy=[],
    pytest=[],
)
"""The default command-line options for all types of repositories."""

common_config = _config.Config(
    opts=common_command_options.copy(),
    sessions=[
        "formatting",
        "flake8",
        "mypy",
        "pylint",
        "pytest_min",
        "pytest_max",
    ],
    source_paths=[
        "src",
    ],
    extra_paths=[
        "benchmarks",
        "docs",
        "examples",
        "noxfile.py",
        "tests",
    ],
)
"""The default configuration for all types of repositories."""

actor_command_options: _config.CommandsOptions = common_command_options.copy()
"""The default command-line options for actors."""

actor_config: _config.Config = common_config.copy()
"""The default configuration for actors."""

api_command_options: _config.CommandsOptions = common_command_options.copy()
"""The default command-line options for APIs."""

api_config: _config.Config = common_config.copy()
"""The default configuration for APIs.

Same as [`common_config`][..common_config], but with an empty `source_paths` (as the
sources are automatically generated, we don't want to test anything in there).
"""

# We don't check the sources at all because they are automatically generated.
api_config.source_paths = []

app_command_options: _config.CommandsOptions = common_command_options.copy()
"""The default command-line options for applications."""

app_config: _config.Config = common_config.copy()
"""The default configuration for applications."""

lib_command_options: _config.CommandsOptions = common_command_options.copy()
"""The default command-line options for libraries."""

lib_config: _config.Config = common_config.copy()
"""The default configuration for libraries."""

model_command_options: _config.CommandsOptions = common_command_options.copy()
"""The default command-line options for models."""

model_config: _config.Config = common_config.copy()
"""The default configuration for models."""
