# License: {{cookiecutter.license}}
# Copyright © {{copyright_year}} {{cookiecutter.author_name}}

"""Generate the code reference pages."""

from frequenz.repo.config.mkdocs import api_pages

api_pages.generate_python_api_pages("{{cookiecutter | src_path}}", "{{'python-' if cookiecutter.type == 'api'}}reference")
{%- if cookiecutter.type == 'api' %}
api_pages.generate_protobuf_api_pages()
{%- endif %}
