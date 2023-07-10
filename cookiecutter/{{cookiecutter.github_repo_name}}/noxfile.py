# License: {{cookiecutter.license}}
# Copyright © {% now 'utc', '%Y' %} {{cookiecutter.author_name}}

"""Configuration file for nox."""

from frequenz.repo.config import RepositoryType, nox

nox.configure(RepositoryType.{{cookiecutter.type | upper}})
