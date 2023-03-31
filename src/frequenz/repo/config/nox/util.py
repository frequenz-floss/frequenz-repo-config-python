"""TODO."""


import pathlib
import tomllib
from collections.abc import Iterable
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
    return [item for sublist in iterables for item in sublist]


def existing_paths(paths: Iterable[str], /) -> Iterable[pathlib.Path]:
    """Filter paths to only leave valid paths that exist.

    Args:
        paths: The paths to check and filter.

    Returns:
        An iterable with the valid paths as `pathlib.Path` objects.

    Example:
        >>> assert list(existing_paths([".", "/fake"])) == [pathlib.Path(".")]
    """
    return (p for p in map(pathlib.Path, paths) if p.exists())


def path_to_package(path: pathlib.Path, root: pathlib.Path | None = None) -> str:
    """Convert paths to Python package names.

    Paths should exist and be either a directory or a file ending with `.py`
    (otherwise this function will raise an error).
    The `root` and `path` are concatenated when performing the check.

    Directory separators in `path` are replaced with `.` and the `.py` suffix
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
    assert real_path.is_dir() or real_path.suffix == ".py"

    if real_path.suffix == ".py":
        path = path.with_suffix("")
    return path.as_posix().replace("/", ".")


def find_toplevel_package_dirs(
    path: pathlib.Path, /, *, root: pathlib.Path | None = None
) -> Iterable[pathlib.Path]:
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

    Raises:
        RuntimeError: If minimun dependencies are not properly
            set in pyproject.toml.

    Returns:
        the minimun dependencies defined in pyproject.toml.

    """
    with open("pyproject.toml", "rb") as toml_file:
        data = tomllib.load(toml_file)

    dependencies = data.get("project", {}).get("dependencies", {})
    if not dependencies:
        raise RuntimeError(f"No dependencies found in file: {toml_file.name}")

    min_deps: list[str] = []
    for dep in dependencies:
        min_dep = dep.split(",")[0]
        if any(op in min_dep for op in (">=", "==")):
            min_deps.append(min_dep.replace(">=", "=="))
        else:
            raise RuntimeError(f"Minimum requirement is not set: {dep}")
    return min_deps
