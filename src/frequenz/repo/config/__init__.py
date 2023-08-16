# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

r"""Frequenz project setup tools and common configuration.

The tools are provided to configure the main types of repositories most commonly used at
Frequenz, defined in
[`frequenz.repo.config.RepositoryType`][].

- actor: SDK actors
- api: gRPC APIs
- app: SDK applications
- lib: General purpose Python libraries
- model: SDK machine learning models

# Common

## `nox` (running tests and linters)

### Writing the `noxfile.py`

Projects wanting to use `nox` to run lint checkers and other utilities can use
the [`frequenz.repo.config.nox`][] package.

When writing the `noxfile.py` you should import the `nox` module from this
package and use the [`frequenz.repo.config.nox.configure`][] function,
which will configure all nox sessions.

To use the default options, you should call `configure()` using one of the [repository
types][frequenz.repo.config.RepositoryType].  For example:

```python
from frequenz.repo.config import RepositoryType, nox

nox.configure(RepositoryType.LIB)
```

Again, make sure to pick the correct project typedefault configuration based on the type of your
project (`actor_config`, `api_config`, `app_config`, `lib_config`, `model_config`).

If you need to use some custom configuration, you can start from the default settings in
the [`frequenz.repo.config.nox.default`][] module,
[copying][frequenz.repo.config.nox.config.Config.copy] it and changing whatever you
need to customize.  For example:

```python
from frequenz.repo.config import nox
from frequenz.repo.config.nox import default

config = default.lib_config.copy()
config.opts.black.append("--diff")
nox.configure(config)
```

If you need further customization or to define new sessions, you can use the
following modules:

- [`frequenz.repo.config.nox.config`][]: Low-level utilities to configure nox
  sessions. It defines the `Config` and CommandsOptions` classes and the actual
  implementation of the `configure()` function. It also defines the `get()`
  function, which can be used to get the currently used configuration object.

- [`frequenz.repo.config.nox.session`][]: Predefined nox sessions. These are
  the sessions that are used by default.

- [`frequenz.repo.config.nox.util`][]: General purpose utility functions.

### `pyproject.toml` configuration

All sessions configured by this package expect the `pyproject.toml` file to
define specific *dev* dependencies that will be used by the different `nox`
sessions.

The following optional dependencies are used and must be defined:

- `dev-docstrings`: Dependencies to lint the documentation.

  At least these packages should be included:

  - `pydocstyle`: To check the docstrings' format.
  - `darglint`: To check the docstrings' content.

- `dev-formatting`: Dependencies to check the code's formatting.

  At least these packages should be included:

  - `black`: To check the code's formatting.
  - `isort`: To check the imports' formatting.

- `dev-mypy`: Dependencies to run `mypy` to check the code's type annotations.

  At least these packages should be included:

  - `mypy`: To check the code's type annotations.

- `dev-pylint`: Dependencies to run `pylint` to lint the code.

  At least these packages should be included:

  - `pylint`: To lint the code.

- `dev-pytest`: Dependencies to run the tests using `pytest`.

  At least these packages should be included:

  - `pytest`: To run the tests.

For some of these you should install too any other dependencies that are used
by the project. For example, if the project uses `pytest-asyncio`, you should
include it in the `dev-pytest` optional dependency.

It is also recommended, but not required, to provide a global `dev` optional
dependency that includes all the other optional dependencies, so users can
install all the dependencies needed while developing the project without having
to run `nox`, which might be a bit slow if you want to do quick iterations.

```console
$ pip install -e .[dev]
...
$ pytest
...
```

Here is a sample `pyproject.toml` file that defines all the optional
dependencies:

```toml
[project]
name = "my-package"
# ...

[project.optional-dependencies]
dev-docstrings = ["pydocstyle == 6.3.0", "darglint == 1.8.1"]
dev-formatting = ["black == 23.3.0", "isort == 5.12.0"]
dev-mkdocs = [
  "mike == 1.1.2",
  "mkdocs-gen-files == 0.5.0",
  "mkdocs-literate-nav == 0.6.0",
  "mkdocs-material == 9.1.16",
  "mkdocs-section-index == 0.3.5",
  "mkdocstrings[python] == 0.22.0",
]
dev-mypy = [
  "mypy == 1.1.1",
  # For checking tests
  "my-package[dev-mkdocs,dev-pytest]",
]
dev-pylint = [
  "pylint == 2.17.1",
  "pylint-google-style-guide-imports-enforcing == 1.3.0",
  # For checking tests
  "my-package[dev-mkdocs,dev-pytest]",
]
dev-pytest = [
  "pytest == 7.2.2",
  "pytest-asyncio == 0.21.0",
  "pytest-mock == 3.10.0",
]
dev = [
  "my-package[dev-mkdocs,dev-docstrings,dev-formatting,dev-mypy,dev-nox,dev-pylint,dev-pytest]",
]
```

## `mkdocs` (generating documentation)

### API reference generation

The API documnentation can be automatically generated from the source files using the
[`frequenz.repo.config.mkdocs`][] package as when run as a
[`mkdocs-gen-files`](https://oprypin.github.io/mkdocs-gen-files/) plugin script.

To enable it you just need to make sure the `mkdocs-gen-files`, `mkdocs-literate-nav`
and `mkdocstrings[python]` packages are installed (look at the `pyproject.toml`
configuration in the `nox` section) and add the following configuration to the
`mkdocs.yml` file:

```yaml
plugins:
  - gen-files:
      scripts:
        - path/to/my/custom/script.py
```

By default this script will look for files in the `src/` directory and generate the
documentation files in the `python-reference/` directory inside `mkdocs` output directory
(`site` by defaul).

If you need to customize the above paths, you can create a new script to use with the
`mkdocs-gen-files` plugin as follows:

```python
from frequenz.repo.config import mkdocs

mkdocs.generate_python_api_pages("my_sources", "API")
```

Where `my_sources` is the directory containing the source files and `API` is the
directory where to generate the documentation files (relative to `mkdocs` output
directory).

And then replace this configuration in the `mkdocs.yml` file:

```yaml
plugins:
  - gen-files:
      scripts:
        - path/to/my/custom/script.py
```

## `pytest` (running tests)

### Linting examples in the source code's *docstrings*

To make sure the examples included in your source code's *docstrings* are valid, you can
use [`pytest`](https://pypi.org/project/pytest/) to automatically collect all the
examples wrapped in triple backticks (````python`) within our docstrings and validate
them using [`pylint`](https://pypi.org/project/pylint/).

To do so there is some setup that's needed:

1. Add a `conftest.py` file to the root directory containing your source code with the
   following contents:

    ```python
    from frequenz.repo.config.pytest import examples
    from sybil import Sybil

    pytest_collect_file = Sybil(**examples.get_sybil_arguments()).pytest()
    ```

    Unfortunately, because of how Sybil works, the [`Sybil`][sybil.Sybil] class needs to
    be instantiated in the `conftest.py` file. To easily do this, the convenience
    function
    [`get_sybil_arguments()`][frequenz.repo.config.pytest.examples.get_sybil_arguments]
    is provided to get the arguments to pass to the `Sybil()` constructor to be able to
    collect and lint the examples.

2. Add the following configuration to your `pyproject.toml` file (see
   the [`nox` section](#pyprojecttoml-configuration) for details on how to configure
   dependencies to play nicely with `nox`):

    ```toml
    [project.optional-dependencies]
    # ...
    dev-pytest = [
        # ...
        "frequenz-repo-config[extra-lint-examples] == 0.5.1",
    ]
    # ...
    [[tool.mypy.overrides]]
    module = [
        # ...
        "sybil",
        "sybil.*",
    ]
    ignore_missing_imports = true
    # ...
    [tool.pytest.ini_options]
    testpaths = [
        # ...
        "src",
    ]
    ```

   This will make sure that you have the appropriate dependencies installed to run the
   the tests linting and that `mypy` doesn't complain about the `sybil` module not being
   typed.

3. Exclude the `src/conftest.py` file from the distribution package, as it shouldn't be
   shipped with the code, it is only for delelopment purposes. To do so, add the
   following line to the `MANIFEST.in` file:

    ```
    # ...
    exclude src/conftest.py
    ```

Now you should be able to run `nox -s pytest` (or `pytest` directly) and see the tests
linting the examples in your code's *docstrings*.

# APIs

## Protobuf configuation

Support is provided to generate files from *protobuf* files.  To do this, it is possible
to configure the options to use while generating the files for different purposes
(language bindings, documentation, etc.).

The configuration can be done in the `pyproject.toml` file as follows:

```toml
[tool.frequenz_repo_config.protobuf]
# Location of the proto files relative to the root of the repository (default: "proto")
proto_path = "proto_files"
# Glob pattern to use to find the proto files in the proto_path (default: "*.proto")
proto_glob = "*.prt"  # Default: "*.proto"
# List of paths to pass to the protoc compiler as include paths (default:
# ["submodules/api-common-protos", "submodules/frequenz-api-common/proto"])
include_paths = ["submodules/api-common-protos"]
# Path where to generate the Python files (default: "py")
py_path = "generated"
# Path where to generate the documentation files (default: "protobuf-reference")
docs_path = "API"
```

If the defaults are not suitable for you (for example you need to use more or less
submodules or your proto files are located somewhere else), please adjust the
configuration to match your project structure.

### `mkdocs` API reference generation

If your project provides *protobuf* files, you can also generate the API
documentation for them adding one more line to the script provided in the common
section:

```python
from frequenz.repo.config import mkdocs

mkdocs.generate_python_api_pages("my_sources", "API-py")
mkdocs.generate_protobuf_api_pages()
```

This will use the configuration in the `pyproject.toml` file and requires `docker` to
run (it uses the `pseudomuto/protoc-gen-doc` docker image.

### `setuptools` gRPC support

When configuring APIs it is assumed that they have a gRPC interface.

The project structure is assumed to be as described in the *Protobuf configuration*
section plus the following:

- `pytests/`: Directory containing the tests for the Python code.
- `submodules/api-common-protos`: Directory containing the Git submodule with the
  `google/api-common-protos` repository.
- `submodules/frequenz-api-common`: Directory containing the Git submodule with the
  `frequenz-floss/frequenz-api-common` repository.

Normally Frequenz APIs use basic types from
[`google/api-common-protos`](https://github.com/googleapis/api-common-protos) and
[`frequenz-floss/frequenz-api-common`](https://github.com/frequenz-floss/frequenz-api-common),
so you need to make sure the proper submodules are added to your project:

```sh
mkdir submodules
git submodule add https://github.com/googleapis/api-common-protos.git \
        submodules/api-common-protos
git submodule add https://github.com/frequenz-floss/frequenz-api-common.git \
        submodules/frequenz-api-common
git commit -m "Add api-common-protos and frequenz-api-common submodules" submodules
```

Then you need to add this package as a build dependency and a few extra
dependencies to your project, for example:

```toml
requires = [
  "setuptools >= 67.3.2, < 68",
  "setuptools_scm[toml] >= 7.1.0, < 8",
  "frequenz-repo-config[api] >= 0.5.1, < 0.6.0",
]
build-backend = "setuptools.build_meta"

[project]
dependencies = [
  "frequenz-api-common >= 0.2.0, < 0.3.0",
  "googleapis-common-protos >= 1.56.2, < 2",
  "grpcio >= 1.51.1, < 2",
]
```

Note the `api` extra in `frequenz-repo-config[api]`, this will ensure all
dependencies to build the protocol files will be installed when building the
package. Of course you need to replace the version numbers with the correct
ones too.

You should also add the following configuration to your `pyproject.toml` file
to make sure the generated files are included in the wheel:

```toml
[tool.setuptools.package-dir]
"" = "py"

[tool.setuptools.package-data]
"*" = ["*.pyi"]

[tools.pytest.ini_options]
testpaths = ["pytests"]
```

Finally you need to make sure to include the generated `*.pyi` files in the
source distribution, as well as the Google api-common-protos files, as it
is not handled automatically yet
([#13](https://github.com/frequenz-floss/frequenz-repo-config-python/issues/13)).
Make sure to include these lines in the `MANIFEST.in` file:

```
recursive-include submodules/api-common-protos/google *.proto
recursive-include submodules/frequenz-api-common/proto *.proto
```

Please adapt the instructions above to your project structure if you need to change the
defaults.
"""

from ._core import RepositoryType

__all__ = [
    "RepositoryType",
]
