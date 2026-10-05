# License: MIT
# Copyright © 2026 Frequenz Energy-as-a-Service GmbH

"""Tests for the examples module."""

from pathlib import Path

import pytest
from sybil import Document, Sybil
from sybil.example import SybilFailure

from frequenz.repo.config.pytest import examples

_SOURCE = '''\
"""Module docstring.

Example:

```{info}
# pylint: disable=abstract-method
import collections.abc

x: collections.abc.Sequence[int] = []{extra}
```
"""
'''


def _parse(path: Path, info: str, extra: str = "") -> Document:
    path.write_text(_SOURCE.format(info=info, extra=extra), encoding="utf-8")
    return Sybil(**examples.get_sybil_arguments()).parse(path)


@pytest.mark.parametrize(
    "info",
    [
        "python",
        'python show_lines="2:"',
        'python {show_lines="2:"}',
        '{.python show_lines="2:"}',
        'python title="some file.py"',
        'python hl_lines="1 2"',
        'python linenums="1"',
        "{ .python .annotate }",
    ],
)
def test_python_blocks_are_parsed(tmp_path: Path, info: str) -> None:
    """Test that Python blocks are parsed, even with options after the language."""
    document = _parse(tmp_path / "example.py", info)
    assert len(list(document)) == 1


@pytest.mark.parametrize(
    "info",
    ["text", 'text show_lines="1"', "python3", "pythonx", "py", "{.text}", ""],
)
def test_other_blocks_are_not_parsed(tmp_path: Path, info: str) -> None:
    """Test that blocks in other languages are still ignored."""
    document = _parse(tmp_path / "example.py", info)
    assert not list(document)


def test_blocks_with_options_are_linted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that the whole block is linted, including lines hidden with `show_lines`."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(tmp_path)
    path = tmp_path / "example.py"
    # The block has 5 lines: with `show_lines=":4"`, the last one is hidden, and it's
    # the one with the pylint error
    document = _parse(path, 'python show_lines=":4"', extra="\nundefined_name")
    (example,) = list(document)
    with pytest.raises(SybilFailure, match="undefined-variable"):
        example.evaluate()
