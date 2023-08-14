# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Validate docstring code examples.

Code examples are often wrapped in triple backticks (```) within docstrings.
This plugin extracts these code examples and validates them using pylint.
"""

from sybil import Sybil

from frequenz.repo.config.pytest import examples

pytest_collect_file = Sybil(**examples.get_sybil_arguments()).pytest()
