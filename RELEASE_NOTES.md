# Frequenz Repository Configuration Release Notes

## Summary

This release replaces [`darglint`](https://github.com/terrencepreilly/darglint) (not maintained anymore) with [`pydoclint`](https://github.com/jsh9/pydoclint) which brings performance and checks improvements. It also adds basic `flake8` checks and `mypy` fixes.

## Upgrading

- `flake8` basic checks are enabled now. Most are already covered by `pylint`, but there are a few differences, so you might need to fix your code if `flake8` find some issues.

- `darglint`:

  * Replaced by `pydoclint`, `pydoclint` can find a few more issues than `darglint`, so your code might need adjusting.

  * It is recommended to remove the `darglint` configuration file `.darglint` and the `darglint` `pip` package, if it is kept installed, it will make `flake8` run extremely slowly even if not used: `pip uninstall darglint`) and rebuild you `nox` *venvs* if you use `-R`.

- If you are upgrading without regenerating the cookiecutter templates, you'll need to adjust the dependencies accordingly.

- `nox`: The `Config.package_args()` method was removed.

- `mypy`

    * Options must be specified in the `pyproject.toml` file, including the option `packages` specifying the package containing the source code of the project. The documentation was updated to suggest the recommended options.

    * Dependencies on *stubs* for running the type check need to be specified manually in the `pyproject.toml` file, so they can be pinned (before they were installed automatically by `mypy`.

    * The `mypy` `nox` session runs `mypy` 2 times, one without options to check the package including the sources, and one with the paths of development paths (`tests`, `benchmarks`, etc.).

    To migrate existing projects:

    1. Add the recommended options (previously specified in the default options object):

        ```toml
        [tool.mypy]
        explicit_package_bases = true
        namespace_packages = true
        packages = ["<package.name>"]  # For example: "frequenz.repo.config" for this package
        strict = true
        ```

    2. Find out which *stubs* were previously installed automatically by `mypy`:

        ```sh
        python -m venv tmp_venv
        . tmp_venv/bin/activate
        pip install -e .[dev-mypy]
        mypy --install-types
        deactivate
        ```

    3. Look at the list of packages it offers to install and answer "no".

    4. Search for the latest package version for those packages in https://pypi.org/project/<package-name>/

    5. Edit the `pyproject.toml` file to add those dependencies in `dev-mypy`, for example:

        ```toml
        [project.optional-dependencies]
        dev-mypy = [
        "mypy == 1.5.1",
        "types-setuptools == 68.1.0.0",
        # ...
        ```

### Cookiecutter template

- CI: The `nox` job now uses a matrix to run the different `nox` sessions in parallel. If you use branch projection with the `nox` job you need to update the rules to include each matrix job.

- See the general upgrading section.

## New Features

- `flake8` is now used to check the files.

- `darlint` was replaced by `pydoclint`, which is way faster and detect more issues.

- `nox`: The `Config.path_args()` method now accepts two optional arguments to control with paths to include.

### Cookiecutter template

- Now dependabot updates will be done weekly and grouped by *required* and *optional* for minor and patch updates (major updates are still done individually for each dependency).

- ci: Add debug information when installing pip packages.

  The output of `pip freeze` is printed to be able to more easily debug different behaviours between GitHub workflow runs and local runs.

- `mypy`: Add a commented out `no-incremental` option, which makes the run slower but prevents some issues with `mypy` giving different results on different runs.

- See the general new features section.
