"""TODO."""

from . import config as _config

common_command_options: _config.CommandsOptions = _config.CommandsOptions(
    black=[
        "--check",
    ],
    darglint=[
        "-v2",  # for verbose error messages.
    ],
    isort=[
        "--check",
    ],
    mypy=[
        "--install-types",
        "--namespace-packages",
        "--non-interactive",
        "--explicit-package-bases",
        "--strict",
    ],
    # SDK: pylint "--extension-pkg-whitelist=pydantic"
    pytest=[
        "-W=all",
        "-vv",
    ],
)

common_config = _config.Config(
    opts=common_command_options.copy(),
    sessions=[
        "formatting",
        "mypy",
        "pylint",
        "docstrings",
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

lib_command_options: _config.CommandsOptions = common_command_options.copy()

lib_config: _config.Config = common_config.copy()

api_command_options: _config.CommandsOptions = common_command_options.copy()

api_config: _config.Config = common_config.copy()

actor_command_options: _config.CommandsOptions = common_command_options.copy()

actor_config: _config.Config = common_config.copy()

app_command_options: _config.CommandsOptions = common_command_options.copy()

app_config: _config.Config = common_config.copy()
