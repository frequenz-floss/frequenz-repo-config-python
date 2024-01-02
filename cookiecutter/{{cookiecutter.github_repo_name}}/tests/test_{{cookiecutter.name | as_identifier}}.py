# License: {{cookiecutter.license}}
# Copyright © {{copyright_year}} {{cookiecutter.author_name}}

"""Tests for the {{cookiecutter.python_package}} package."""

{%- if cookiecutter.type == "api" %}


def test_package_import() -> None:
    """Test that the package can be imported."""
    # pylint: disable=import-outside-toplevel
    from frequenz.api import {{cookiecutter.name | as_identifier}}

    assert {{cookiecutter.name | as_identifier}} is not None


def test_module_import_components() -> None:
    """Test that the modules can be imported."""
    # pylint: disable=import-outside-toplevel
    from frequenz.api.{{cookiecutter.name | as_identifier}} import {{cookiecutter.name | as_identifier}}_pb2

    assert {{cookiecutter.name | as_identifier}}_pb2 is not None

    # pylint: disable=import-outside-toplevel
    from frequenz.api.{{cookiecutter.name | as_identifier}} import {{cookiecutter.name | as_identifier}}_pb2_grpc

    assert {{cookiecutter.name | as_identifier}}_pb2_grpc is not None
{%- else %}
import pytest

from {{cookiecutter.python_package}} import delete_me


def test_{{cookiecutter.name | as_identifier}}_succeeds() -> None:  # TODO(cookiecutter): Remove
    """Test that the delete_me function succeeds."""
    assert delete_me() is True


def test_{{cookiecutter.name | as_identifier}}_fails() -> None:  # TODO(cookiecutter): Remove
    """Test that the delete_me function fails."""
    with pytest.raises(RuntimeError, match="This function should be removed!"):
        delete_me(blow_up=True)
{%- endif %}
