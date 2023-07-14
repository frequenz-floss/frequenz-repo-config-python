# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""General purpose utilities.

This module contains general purpose utilities that are used by the other
modules in this package.
"""


import pathlib as _pathlib
import tomllib as _tomllib
from collections.abc import Iterable, Mapping
from typing import TypeVar

_T = TypeVar("_T")


def flatten(iterables: Iterable[Iterable[_T]], /) -> Iterable[_T]:
    """Flatten an iterable of iterables into one iterable with all the elements.

    Args:
        iterables: The iterables to flatten.

    Returns:
        The flattened iterable.

    Example:
        >>> assert list(flatten([(1, 2), (3, 4)]) == [1, 2, 3, 4]
    """
    return (item for sublist in iterables for item in sublist)


def replace(iterable: Iterable[_T], replacements: Mapping[_T, _T], /) -> Iterable[_T]:
    """Replace elements in an iterable.

    Args:
        iterable: The iterable to replace elements in.
        replacements: A mapping of elements to replace with other elements.

    Yields:
        The next element in the iterable, with the replacements applied.

    Example:
        >>> assert list(replace([1, 2, 3], {1: 4, 2: 5})) == [4, 5, 3]
    """
    for item in iterable:
        if item in replacements:
            yield replacements[item]
        else:
            yield item


def deduplicate(iterable: Iterable[_T], /) -> Iterable[_T]:
    """Filter out duplicates from an iterable preserving the original iterable order.

    Args:
        iterable: The iterable to remove duplicates from.

    Returns:
        The elements of `iterable`, without duplicates but preserving order.
    """
    # We can't use a set() here because sets don't preserve order.  We use this hack
    # with dict.fromkeys() because dicts do preserve order in Python 3.7+.
    return dict.fromkeys(iterable).keys()


def existing_paths(paths: Iterable[str], /) -> Iterable[_pathlib.Path]:
    """Filter paths to only leave valid paths that exist and are unique.

    Args:
        paths: The paths to check and filter.

    Returns:
        An iterable with the valid paths as `pathlib.Path` objects.

    Example:
        >>> assert list(existing_paths([".", "/fake"])) == [pathlib.Path(".")]
    """
    return deduplicate(p for p in map(_pathlib.Path, paths) if p.exists())


def is_python_file(path: _pathlib.Path, /) -> bool:
    """Check if a path is a Python file.

    Args:
        path: The path to check.

    Returns:
        `True` if the path is a Python file, `False` otherwise.
    """
    return path.suffix in (".py", ".pyi")


def path_to_package(path: _pathlib.Path, root: _pathlib.Path | None = None) -> str:
    """Convert paths to Python package names.

    Paths should exist and be either a directory or a file ending with `.pyi?`
    (otherwise this function will assert). The `root` and `path` are
    concatenated when performing the check.

    Directory separators in `path` are replaced with `.` and the `.pyi?` suffix
    is removed (if present).

    Args:
        path: The path to convert.
        root: The root where the path is located. If `None`, then it is
            considered present in the current working directory.

    Returns:
        The package name based on `path`.

    Examples:
        * `src/frequenz/pkg` (`root="src"`) will be converted to `frequenz.pkg`.
        * `noxfile.py` (without `root`) will be converted to `noxfile`.
    """
    real_path = path
    if root is not None:
        real_path = root / path
    assert real_path.is_dir() or is_python_file(real_path)

    if is_python_file(real_path):
        path = path.with_suffix("")
    return path.as_posix().replace("/", ".")


def find_toplevel_package_dirs(
    path: _pathlib.Path, /, *, root: _pathlib.Path | None = None
) -> Iterable[_pathlib.Path]:
    """Find top-level packages directories in a `path`.

    Searches recursively for the top-level packages in `path`, relative to
    `root`.

    Args:
        path: The path to look for python packages.
        root: The part of the path that is considered the root and will be
            removed from the resulting path. If `None` then `path` is used as
            `root`.

    Returns:
        The top-level paths that contains a `__init__.py` file, with `root`
        removed.

    Examples:
        If we have a directory like the following:

        ```
        .
        ├── noxfile.py
        └── src
            └── frequenz
                └── repo
                    └── config
                        ├── __init__.py
                        ├── nox
                        │   ├── config.py
                        │   ├── default.py
                        │   ├── __init__.py
                        │   ├── session.py
                        │   └── util.py
                        └── setuptools.py
        ```

        Then calling `find_toplevel_package_dirs(pathlib.Path("src"))` will
        return an iterator producing: `["frequenz/repo/config"]`.
    """
    if root is None:
        root = path
    # Bail out early if it is a directory with a __init__.py to avoid getting
    # sub-packages
    if (path / "__init__.py").exists():
        return [path.relative_to(root)]
    if path.is_dir():
        return flatten(
            [find_toplevel_package_dirs(p, root=root) for p in path.iterdir()]
        )
    return ()


def min_dependencies() -> list[str]:
    """Extract the minimum dependencies from pyproject.toml.

    Returns:
        The minimun dependencies defined in pyproject.toml.

    Raises:
        RuntimeError: If minimun dependencies are not properly set in pyproject.toml.
    """
    with open("pyproject.toml", "rb") as toml_file:
        data = _tomllib.load(toml_file)

    min_deps: list[str] = []

    dependencies = data.get("project", {}).get("dependencies", {})
    if not dependencies:
        return min_deps

    for dep in dependencies:
        min_dep = dep.split(",")[0]
        if any(op in min_dep for op in (">=", "==", "@")):
            min_deps.append(min_dep.replace(">=", "=="))
        else:
            raise RuntimeError(f"Minimum requirement is not set: {dep}")
    return min_deps


def discover_paths() -> list[str]:
    """Discover paths to check.

    Discover the paths to check by looking into different sources, like the
    `pyproject.toml` file.

    Currently the following paths are discovered:

    - The `testpaths` option in the `tools.pytest.ini_options` section of
      `pyproject.toml`.

    Returns:
        The discovered paths to check.
    """
    with open("pyproject.toml", "rb") as toml_file:
        data = _tomllib.load(toml_file)

    testpaths: list[str] = (
        data.get("tool", {})
        .get("pytest", {})
        .get("ini_options", {})
        .get("testpaths", [])
    )

    return list(deduplicate(testpaths))
