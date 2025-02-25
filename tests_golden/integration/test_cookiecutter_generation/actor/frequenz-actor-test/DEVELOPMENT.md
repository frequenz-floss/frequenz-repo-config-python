# Development Guide

This document describes how to set up your development environment and how to
run the tests and checks, in case you want to customize the project to your
needs or in case you want to contribute to it.

This project is implemented in Python.

## Tooling

The project uses several tools to ensure code quality and consistency:

* [mypy] for static type checking.
* [flake8] (with some plugins) and [pylint] for code style and quality
  checking and linting.
* [black] and [isort] for code formatting.
* [pytest] for running tests.
* [mkdocs] for building the documentation and [mike] for managing multiple
  versions of the documentation. We also use [mkdocs-material] as the theme and
  [mkdocstrings] to generate the API documentation.
* [nox] for automating the execution of these tools.
* [repo-config] for updating common files in all projects and ensuring
  consistency across repositories.
* [setuptools] to manage the project and its dependencies.

### Project configuration

We use [setuptools] to manage the project and its dependencies. [setuptools] is
also a complex and powerful framework.

We do all configuration in the `pyproject.toml` file, using [PEP
517](https://peps.python.org/pep-0517/) to define the project configuration,
and also include other tools configuration in it, like [pytest], [mypy],
[flake8], [pylint], [black], [isort], etc., so is it probably worth having
a look at `pyproject.toml` to get familiar with the different tool options and
dependencies used by the project.

Usually all you need to know for the day-to-day development is how to add,
remove and upgrade dependencies, and how to configure other tools.

Getting to understand how [setuptools] works takes some time, and it is
generally not necessary, but if you need to, the [official user
guide](https://setuptools.pypa.io/en/latest/userguide/index.html) is a good
resource.

### Type checking

We write all our code with
[strict](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict)
type hints, all code must use type annotations, and it is checked using [mypy].

If you are not familiar with type hints and static, there is unforuntally one
main authoritative getting started guide/tutorial, but here are some
recommended reads, varying in depth and focus:

* [Tutorial from The Real Python](https://realpython.com/python-type-checking/)
* [Getting started guide from `mypy`](https://mypy.readthedocs.io/en/stable/getting_started.html)
* [Type hints cheat sheet from `mypy`](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
* [Python `typing` documentation](https://docs.python.org/3/library/typing.html)
* [Static typing specification](https://typing.readthedocs.io/)

> [!WARNING]
> Please note that don't use the deprecated type hints in the
> [`typing`](https://docs.python.org/3/library/typing.html) module, but many
> documentation resources still do.
>
> Use:
>
> * The `|` operator instead of `typing.Union` (`Union[T1, T2, T3]` -> `T1 | T2 | T3`)
> * `| None` instead of `typing.Optional` (`Optional[T]` -> `T | None`)
> * Built-in types (like `list`, `dict`, etc. instead of `List`, `Dict`, etc.)
> * Types from
>   [`collections.abc`](https://docs.python.org/3/library/collections.abc.html),
>   instead of `typing` when they are available there (`Sequence`, `Iterator`,
>   `Awaitable`, etc.)

### Testing

We use [pytest] to run tests. [pytest] is a big and powerful test framework, so
we recommend getting familiar with it if you are not already.

* [Official getting started guide](https://docs.pytest.org/en/stable/getting-started.html)
* [Official how-to guides](https://docs.pytest.org/en/stable/how-to/index.html)
* [Tutorial from The Real Python](https://realpython.com/pytest-python-testing/)

> [!TIP]
> Here are a few recommendations:
>
> * We prefer to keep tests as flat as possible, when nesting is not necessary,
>   avoid [grouping all tests in a file in
>   a class](https://docs.pytest.org/en/stable/getting-started.html#group-multiple-tests-in-a-class).
>   Unless a file is very small, we prefer to split tests in multiple files
>   than having a huge file with many test groups in classes.
> * Use
>   [fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html#how-to-fixtures)
>   to reuse code, test data, etc. as much as possible.
> * Avoid reinventing the wheel, always first search for [available
>   fixtures](https://docs.pytest.org/en/stable/reference/fixtures.html#builtin-fixtures).
>   Also check for [fixtures in third-party
>   plugins](https://docs.pytest.org/en/stable/reference/fixtures.html#built-in-fixtures) if you are using [plugins](https://docs.pytest.org/en/stable/plugins.html).
> * When possible,
>   [parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.htmlhttps://docs.pytest.org/en/stable/how-to/parametrize.html)
>   instead of having for loops in tests to test multiple cases.
> * When you have too many parameters for one test case, consider using
>   a `dataclass` to represent one test case, and have the test accept that
>   `dataclass` as a parameter instead.
> * When parameters are not simple built-in types with an short representation,
>   considering [using
>   IDs](https://docs.pytest.org/en/stable/example/parametrize.html#different-options-for-test-ids)
>   (in the case of a test case `dataclass` you can add a `name` field to it
>   and use `ids=lambda tc: tc.name`).
> * Use [`hypothesis`](https://hypothesis.readthedocs.io/) for property-based
>   testing when applicable.
> * Use [`async-solipsism`](https://github.com/bmerry/async-solipsism) to test
>   async code in a more deterministic and faster way when possible.
> * Use [`time-machine`](https://github.com/adamchainz/time-machine) to test
>   time-dependent code in a more deterministic and faster way.

As you can see `pytest` is huge, so it will take some time to get familiar with
all its features, so be patient if you feel a bit overwhelmed at first.

### Documentation

The documentation stack is also quite complex, and uses many tools. [mkdocs] is
the main framework we use, but it is very low level. [mkdocs-material] is the
theme providing most of the high-level functionality.

So before writing documentation, we strongly recommend getting familiar with
[mkdocs-material]. Being a documentation project, the documentation is great,
so the [getting started
guide](https://squidfunk.github.io/mkdocs-material/getting-started/) is a great
place to start.

All configuration is done via the `mkdocs.yml` file, so it is worth having a
look at it to understand the different options available. In particular the
`theme.features`,
[`plugins`](https://squidfunk.github.io/mkdocs-material/plugins/) and
`markdown_extensions` that are enabled.

Plugins and markdown extensions might be installed separately and dependencies
can be declared explicitly in the `pyproject.toml` file too.

[mkdocstrings] is a plugin used to generate the API documentation from the
[docstring]s in the code. It is also configured in the `mkdocs.yml` file in the
`plugins` section, and it is also a complex and powerful tool, that is composed
of many other plugins and tools. To learn the basics, the [official user
guide](https://mkdocstrings.github.io/usage/) should also be enough. It also
has many options, so it is worth having a look at the `mkdocs.yml` file to
understand the different options used by the project.

## Configuring the local environment

### Verifying the Python version

> [!NOTE]
> These instructions assume you are using a [POSIX compatible
> `sh`](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/sh.html)
> shell.

First, you need to make sure you have Python installed (at least version 3.11):

```console
$ python3 --version
Python 3.11.4
```

If that command doesn't print a version newer than 3.11.0, you'll need to
[download and install Python](https://www.python.org/downloads/) first.

### Getting the code

You first need to clone the repository, for example:

```sh
git clone https://github.com/frequenz-floss/frequenz-actor-test.git
cd frequenz-floss/frequenz-actor-test
```

### Installing the development dependencies

It is recommended to use a virtual environment to manage the dependencies of the
project. You can create a virtual environment with the following commands:

```sh
python3 -m venv .venv
. .venv/bin/activate
```

> [!TIP]
> Using [direnv](https://direnv.net/) can greatly simplify this process as
> it automates the creation, activation, and deactivation of the virtual
> environment. The first time you enable `direnv`, the virtual environment
> will be created, and each time you enter or leave a subdirectory, it will be
> activated and deactivated, respectively.
>
> ```sh
> sudo apt install direnv # if you use Debian/Ubuntu
> echo "layout python python3" > .envrc
> direnv allow
> ```
>
> This will create the virtual environment and activate it automatically for you.

Then you can install the development dependencies using [pip]:

```sh
python -m pip install -e .[dev]
```

* The `-e` is used to do an [*editable*
  install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html),
  which means that changes to the source code will be reflected in the
  installed package without needing to reinstall it.

* The `.` means that the package is installed from the current directory, so we are
  installing the package that we are developing.

* The `[dev]` is a [setuptools]
  [feature](https://setuptools.pypa.io/en/latest/userguide/dependency_management.html#optional-dependencies)
  that allows you to [install
  extra/optional](https://packaging.python.org/en/latest/specifications/dependency-specifiers/#extras)
  dependencies. Which dependencies are installed exactly is defined in the
  `pyproject.toml` file, in the `project.optional-dependencies` section, in
  this case under the `dev` key. This will install all tools needed to develop
  the project ([mypy], [pylint], etc.).

## Running tests and checks

### Running checks using [nox]

To run all the checks and tests, you can use [nox]:

```sh
nox
```

This will create a virtual environment, install the dependencies, and run all
the checks and tests. This is great to make sure you are using the exact
dependencies that are specified in the `pyproject.toml` file, but it might be
time-consuming to install all the dependencies every time, specially when
dependencies hardly change during development. To speed things up you can use:

```sh
nox --install-only
```

For the first time, and then use `nox -R` to reuse the current testing
environment, at the expense of a higher chance to end up with a dirty test
environment.

If you want to test using the exact same dependencies that are installed in the
current environment, you can use:

```sh
nox --no-install --no-venv
```

This is useful to speed up the test cycle when you are sure that the
dependencies are already installed.

> [!TIP]
> You can create an alias to make it easier to run [nox] with the options
> you want. For example, you can add the following line to your shell
> configuration file (e.g., `~/.bashrc`, `~/.zshrc`, etc.):
>
> ```sh
> alias noxl='nox --no-venv --no-install'
> ```
>
> Then you can run `noxl` to run [nox] without creating new virtual
> environments.

### Running tests / checks individually

[nox] use different
[sessions](https://nox.thea.codes/en/stable/config.html#defining-sessions) to
run different checks and tests. You can list all the available sessions using:

```sh
nox -l
```

You can run individual sessions using:

```sh
nox -s <session-name>
```

You can also pass arguments to the sessions using:

```sh
nox -s <session-name> -- <arguments>
```

For example, to run `pylint` only on certain files:

```sh
nox -s pylint -- src/some/file.py
```

> [!NOTE]
> Usually the same tools can be used directly without [nox], but using [nox]
> ensures the correct arguments and configuration are used, and it matches what's
> checked by the CI.


For a better development test cycle you can install the runtime and test
dependencies and run `pytest` manually.

### Testing the documentation

There is no automatic testing for the documentation, to test it you need to
build it to make sure there are no issues with the documentation generation,
and eventually you should look at the generated documentation to make sure it
looks good.

The easiest way to do this is to run a local server with the generated documentation:

```sh
mkdocs serve
```

This will build and serve the generated documentation at
http://127.0.0.1:8000/, and the site will be updated **live** when you change
your files (provided that you used `pip install -e`).

If for some reason you need to inspect the generated documentation, you can use
this instead:

```sh
mkdocs build
```

The files will be generated in the `site/`.

#### Multi-version documentation

> [!NOTE]
> In a normal development workflow, you don't need to worry about
> multi-version documentation, as it is only needed when you want to release
> a new version of the documentation. But in certain situations when working
> on the documentation building itself, you might want to test the
> multi-version documentation locally.

To build multi-version documentation, we use [mike]. If you want to see how
the multi-version sites looks like locally, you can use:

```sh
mike deploy my-version
mike set-default my-version
mike serve
```

[mike] works in mysterious ways. Some basic information:

* `mike deploy` will do a `mike build` and write the results to your **local**
  `gh-pages` branch. `my-version` is an arbitrary name for the local version
  you want to preview.
* `mike set-default` is needed so when you serve the documentation, it goes to
  your newly produced documentation by default.
* `mike serve` will serve the contents of your **local** `gh-pages` branch. Be
  aware that, unlike `mkdocs serve`, changes to the sources won't be shown
  live, as the `mike deploy` step is needed to refresh them.

Be careful not to use `--push` with `mike deploy`, otherwise it will push your
local `gh-pages` branch to the `origin` remote.

That said, if you want to test the actual website in **your fork**, you can
always use `mike deploy --push --remote your-fork-remote`, and then access the
GitHub pages produced for your fork.
## Building distribution packages

You can use [build] the source and binary distribution packages with:

```sh
python -m pip install build
python -m build
```

This is usually not necessary, unless you want to test that the build process
is working correctly, or you want to manually distribute the package.


[protolint]: https://github.com/yoheimuta/protolint
[mypy]: https://mypy.readthedocs.io/
[flake8]: https://flake8.pycqa.org/
[pylint]: https://pylint.pycqa.org/
[black]: https://black.readthedocs.io/
[isort]: https://pycqa.github.io/isort/
[pytest]: https://docs.pytest.org/
[mkdocs]: https://www.mkdocs.org/
[mkdocs-material]: https://squidfunk.github.io/mkdocs-material/
[mkdocstrings]: https://mkdocstrings.github.io/
[mike]: https://github.com/jimporter/mik
[nox]: https://nox.thea.codes/
[repo-config]: https://frequenz-floss.github.io/frequenz-repo-config-python/
[pip]: https://pip.pypa.io/en/stable/
[setuptools]: https://setuptools.pypa.io/
[build]: https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives
[docstring]: https://en.wikipedia.org/wiki/Docstring
