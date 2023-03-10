# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Configuration file for nox."""

from frequenz.repo import config

# Remove the pytest sessions because we don't have tests yet
conf = config.nox.default.lib_config.copy()
conf.sessions = [s for s in conf.sessions if not s.startswith("pytest")]

config.nox.configure(conf)
