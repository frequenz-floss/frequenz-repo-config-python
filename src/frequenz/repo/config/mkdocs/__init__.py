# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tools to manage and generate documentation using `mkdocs`."""

from .api_pages import generate_protobuf_api_pages, generate_python_api_pages

__all__ = [
    "generate_protobuf_api_pages",
    "generate_python_api_pages",
]
