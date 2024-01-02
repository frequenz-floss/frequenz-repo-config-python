# License: {{cookiecutter.license}}
# Copyright © {{copyright_year}} {{cookiecutter.author_name}}

"""Configuration file for nox."""

from frequenz.repo.config import RepositoryType, nox

nox.configure(RepositoryType.{{cookiecutter.type | upper}})
