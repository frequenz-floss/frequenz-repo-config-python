# Frequenz Project Setup Tools

Frequenz project setup tools is a collection of tools and common configurations for setting up and managing different types of repositories in the Frequenz ecosystem. These tools are particularly designed to handle 4 main types of repositories:

- APIs (api)
- Actors (actor)
- Applications (app)
- Libraries (lib)

## Installation

The Frequenz project setup tools can be installed via pip:

~~~bash
pip install frequenz-repo-config
~~~

## Usage

### Common Setup

The tools provide configuration for the `nox` tool to run lint checkers and other utilities. To use the `nox` configuration, you should import the `nox` module from this package and use the `frequenz.repo.config.nox.configure` function. The configure function should be called with one of the default configurations provided in the `frequenz.repo.config.nox.default` module. The default configuration you pick should correspond to the type of your project (`api_config`, `actor_config`, `app_config`, `lib_config`).

The `pyproject.toml` file should be configured to define specific dev dependencies that will be used by the different `nox` sessions. These dependencies include those for linting documentation and code, checking code's type annotations, running `pylint` to lint the code, and running the tests using `pytest`.

Example `pyproject.toml` configuration:

~~~toml
[project]
name = "my-package"

[project.optional-dependencies]
dev-docstrings = ["pydocstyle == 6.3.0", "darglint == 1.8.1"]
dev-formatting = ["black == 23.3.0", "isort == 5.12.0"]
dev-mypy = [ "mypy == 1.1.1", "my-package[dev-pytest]"]
dev-pylint = [ "pylint == 2.17.1", "my-package[dev-pytest]"]
dev-pytest = [ "pytest == 7.2.2"]
dev = [ "my-package[dev-docstrings,dev-formatting,dev-mypy,dev-pylint,dev-pytest]"]
~~~

### APIs Setup

When configuring APIs, it is assumed that they have a gRPC interface. The project structure is assumed to include a `proto/` directory containing the `.proto` files, a `py/` directory containing the Python code, and a `pytests/` directory containing the tests for the Python code. API repositories should not contain any other Python code.

For API repositories, a submodule with the `google/api-common-protos` repository is needed. This submodule can be added to your project using the following commands:

~~~bash
mkdir submodules
git submodule add https://github.com:googleapis/api-common-protos.git submodules/api-common-protos
git commit -m "Add Google api-common-protos submodule" submodules/api-common-protos
~~~

Further configurations for the `pyproject.toml` file and a `MANIFEST.in` file are necessary for API repositories to ensure that generated files are included in the wheel and that the Google api-common-protos files are included in the source distribution.

For more information about the usage of these tools and the configurations needed, please refer to the full project documentation.

## License

This project is licensed under the MIT License.
