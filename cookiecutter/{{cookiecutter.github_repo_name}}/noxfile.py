# License: MIT
# Copyright © {% now 'utc', '%Y' %} {{cookiecutter.author_name}}

"""Configuration file for nox."""

from frequenz.repo.config import nox

nox.configure(nox.default.{{cookiecutter.type}}_config)
