# License: MIT
# Copyright © {% now 'utc', '%Y' %} {{cookiecutter.author_name}}

"""Generate the code reference pages."""

from frequenz.repo.config import mkdocs

mkdocs.generate_api_pages("{{cookiecutter | src_path}}")
