# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Generate the code reference pages."""

from frequenz.repo.config.mkdocs import api_pages

api_pages.generate_python_api_pages("py", "python-reference")
api_pages.generate_protobuf_api_pages()
