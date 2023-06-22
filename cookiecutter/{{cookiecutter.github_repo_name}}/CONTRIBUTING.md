# Contributing to {{cookiecutter.title}}

## Build

You can use `build` to simply build the source and binary distribution:

```sh
python -m pip install build
python -m build
```

## Local development
{%- if cookiecutter.type == "api" %}

You need to make sure you have the `git submodules` updated:

```sh
git submodule update --init
```

### Running protolint

To make sure some common mistakes are avoided and to ensure a consistent style
it is recommended to run `protolint`. After you [installed
`protolint`](https://github.com/yoheimuta/protolint#installation), just run:

```sh
protolint lint proto
```

### Python setup
{%- endif %}

You can use editable installs to develop the project locally (it will install
all the dependencies too):

```sh
python -m pip install -e .
```
{%- if cookiecutter.type == "api" %}

This will also generate the Python files from the `proto/` files and leave them
in `py/`, so you can inspect them.
{%- endif %}

Or you can install all development dependencies (`mypy`, `pylint`, `pytest`,
etc.) in one go too:
```sh
python -m pip install -e .[dev]
```

If you don't want to install all the dependencies, you can also use `nox` to
run the tests and other checks creating its own virtual environments:

```sh
python -m pip install .[dev-noxfile]
nox
```

You can also use `nox -R` to reuse the current testing environment to speed up
test at the expense of a higher chance to end up with a dirty test environment.
{%- if cookiecutter.type == "api" %}

### Upgrading dependencies

If you want to update the dependency `frequenz-api-common`, then you need to:

1. Update the submodule `frequenz-api-common`
2. Update the version of the `frequenz-api-common` package in `pyproject.toml`

The version of `frequenz-api-common` used in both places mentioned above should
be the same.

Here is an example of upgrading the `frequenz-api-common` dependency to version
`v0.2.0`:
```sh
ver="0.2.0"

cd submodules/frequenz-api-common
git remote update
git checkout v${ver}
cd -

sed s/"frequenz-api-common == [0-9]\.[0-9]\.[0-9]"/"frequenz-api-common == ${ver}"/g -i pyproject.toml
```
{%- endif %}

### Running tests / checks individually

For a better development test cycle you can install the runtime and test
dependencies and run `pytest` manually.

```sh
python -m pip install .[dev-pytest]  # included in .[dev] too

# And for example
pytest tests/test_*.py
```

Or you can use `nox`:

```sh
nox -R -s pytest -- test/test_*.py
```

The same appliest to `pylint` or `mypy` for example:

```sh
nox -R -s pylint -- test/test_*.py
nox -R -s mypy -- test/test_*.py
```

## Releasing

These are the steps to create a new release:

1. Get the latest head you want to create a release from.

2. Update the `RELEASE_NOTES.md` file if it is not complete, up to date, and
   remove template comments (`<!-- ... ->`) and empty sections. Submit a pull
   request if an update is needed, wait until it is merged, and update the
   latest head you want to create a release from to get the new merged pull
   request.

3. Create a new signed tag using the release notes and
   a [semver](https://semver.org/) compatible version number with a `v` prefix,
   for example:

   ```sh
   git tag -s --cleanup=whitespace -F RELEASE_NOTES.md v0.0.1
   ```

4. Push the new tag.

5. A GitHub action will test the tag and if all goes well it will create
   a [GitHub
   Release](https://github.com/{{cookiecutter.github_org}}/{{cookiecutter.github_repo_name}}/releases),
   and upload a new package to
   [PyPI](https://pypi.org/project/{{cookiecutter.pypi_package_name}}/)
   automatically.

6. Once this is done, reset the `RELEASE_NOTES.md` with the template:

   ```sh
   cp .github/RELEASE_NOTES.template.md RELEASE_NOTES.md
   ```

   Commit the new release notes and create a PR (this step should be automated
   eventually too).

7. Celebrate!
