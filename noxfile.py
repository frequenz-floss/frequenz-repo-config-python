# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Configuration file for nox."""

from frequenz.repo.config import nox

# Remove the pytest sessions because we don't have tests yet
config = nox.default.lib_config.copy()
config.sessions = [s for s in config.sessions if not s.startswith("pytest")]

nox.configure(config)
