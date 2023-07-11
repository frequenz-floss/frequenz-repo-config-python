# License: {{cookiecutter.license}}
# Copyright © {% now 'utc', '%Y' %} {{cookiecutter.author_name}}

"""Tests for the {{cookiecutter.python_package}} package."""

{%- if cookiecutter.type == "api" %}


def test_package_import() -> None:
    """Test that the package can be imported."""
    # pylint: disable=import-outside-toplevel
    from frequenz.api import {{cookiecutter.name}}

    assert {{cookiecutter.name}} is not None


def test_module_import_components() -> None:
    """Test that the modules can be imported."""
    # pylint: disable=import-outside-toplevel
    from frequenz.api.{{cookiecutter.name}} import {{cookiecutter.name}}_pb2

    assert {{cookiecutter.name}}_pb2 is not None

    # pylint: disable=import-outside-toplevel
    from frequenz.api.{{cookiecutter.name}} import {{cookiecutter.name}}_pb2_grpc

    assert {{cookiecutter.name}}_pb2_grpc is not None
{%- else %}
import pytest

from {{cookiecutter.python_package}} import delete_me


def test_{{cookiecutter.name}}_succeeds() -> None:  # TODO(cookiecutter): Remove
    """Test that the delete_me function succeeds."""
    assert delete_me() is True


def test_{{cookiecutter.name}}_fails() -> None:  # TODO(cookiecutter): Remove
    """Test that the delete_me function fails."""
    with pytest.raises(RuntimeError, match="This function should be removed!"):
        delete_me(blow_up=True)
{%- endif %}
