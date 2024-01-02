#!/bin/bash
# License: {{cookiecutter.license}}
# Copyright © {{copyright_year}} {{cookiecutter.author_name}}
{% raw -%}
set -e

echo "System details:" $(uname -a)
echo "Machine:" $(uname -m)

exec "$@"
{%- endraw %}
