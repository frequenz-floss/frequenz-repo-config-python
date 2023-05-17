# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Base types used accross the project."""

import enum as _enum


class RepositoryType(_enum.Enum):
    """Supported types of repository."""

    ACTOR = "actor"
    """SDK actor repository."""

    API = "api"
    """gRPC API repository."""

    APP = "app"
    """SDK application repository."""

    LIB = "lib"
    """General purpose library repository."""

    MODEL = "model"
    """SDK machine learning model repository."""
