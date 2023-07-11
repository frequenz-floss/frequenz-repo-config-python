# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the test package."""


def test_package_import() -> None:
    """Test that the package can be imported."""
    # pylint: disable=import-outside-toplevel
    from frequenz.api import test

    assert test is not None


def test_module_import_components() -> None:
    """Test that the modules can be imported."""
    # pylint: disable=import-outside-toplevel
    from frequenz.api.test import test_pb2

    assert test_pb2 is not None

    # pylint: disable=import-outside-toplevel
    from frequenz.api.test import test_pb2_grpc

    assert test_pb2_grpc is not None
