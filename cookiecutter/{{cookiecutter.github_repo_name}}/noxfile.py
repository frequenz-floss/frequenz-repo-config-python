# License: MIT
# Copyright © {% now 'utc', '%Y' %} Frequenz Energy-as-a-Service GmbH

"""Configuration file for nox."""

from frequenz.repo.config import nox

nox.configure(nox.default.{{cookiecutter.type}}_config)
