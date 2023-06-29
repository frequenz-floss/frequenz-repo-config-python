# License: MIT
# Copyright © {% now 'utc', '%Y' %} {{cookiecutter.author_name}}

"""Configuration file for nox."""

from frequenz.repo.config import nox
from frequenz.repo.config.nox import default

nox.configure(default.{{cookiecutter.type}}_config)
