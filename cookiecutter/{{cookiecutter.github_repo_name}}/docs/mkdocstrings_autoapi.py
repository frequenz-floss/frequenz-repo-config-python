# License: MIT
# Copyright © {% now 'utc', '%Y' %} {{cookiecutter.author_name}}

"""Generate the code reference pages."""

from frequenz.repo.config import mkdocs

mkdocs.generate_python_api_pages("{{cookiecutter | src_path}}", "{{'python-' if cookiecutter.type == 'api'}}reference")
{%- if cookiecutter.type == 'api' %}
mkdocs.generate_protobuf_api_pages()
{%- endif %}
