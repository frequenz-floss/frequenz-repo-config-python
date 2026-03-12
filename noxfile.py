# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Configuration file for nox."""

from frequenz.repo.config import nox
from frequenz.repo.config.nox import default

config = default.lib_config.copy()
config.extra_paths.extend(
    [
        ".github/cookiecutter-migrate.template.py",
        "cookiecutter/hooks",
        "cookiecutter/local_extensions.py",
        "cookiecutter/migrate.py",
    ]
)
nox.configure(config)
