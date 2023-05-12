# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Base types used accross the project."""

import enum


class RepositoryType(enum.Enum):
    """Supported types of repository."""

    ACTOR = "actor"
    """Actor repository."""

    API = "api"
    """API repository."""

    APP = "app"
    """App repository."""

    LIB = "lib"
    """Library repository."""
