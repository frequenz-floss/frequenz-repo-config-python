# Frequenz Repository Configuration

[![Build Status](https://github.com/frequenz-floss/frequenz-repo-config-python/actions/workflows/ci.yaml/badge.svg)](https://github.com/frequenz-floss/frequenz-repo-config-python/actions/workflows/ci.yaml)
[![PyPI Package](https://img.shields.io/pypi/v/frequenz-repo-config)](https://pypi.org/project/frequenz-repo-config/)
[![Docs](https://img.shields.io/badge/docs-latest-informational)](https://frequenz-floss.github.io/frequenz-repo-config-python/)

## Introduction

This is a highly opinionated set of tools and configurations to set up a Python
repository for [Frequenz](https://frequenz.com) projects.

It offers:

* [Cookiecutter] templates for scaffolding new projects
* Trivial build of `noxfile.py` with some predefined sessions that include all
  common checks.
* Tools to build protobuf/grpc files as Python, including type information.

## Supported Platforms

The following platforms are officially supported (tested):

- **Python:** 3.11
- **Operating System:** Ubuntu Linux 20.04
- **Architectures:** amd64, arm64

## Quick Example

To start a new project, you should first [install
Cookiecutter](https://cookiecutter.readthedocs.io/en/stable/installation.html).
It is normally available in any Linux distribution, but some have a very old
version (for example, Ubuntu/Debian). You can [check which version your distro
has on Repology](https://repology.org/project/cookiecutter/versions). You need
**at least version 2.4.0**. To ensure you get an up-to-date version, you can
always use `pip` and install it in a `venv`:

```console
$ python -m venv cookiecutter
$ cd cookiecutter
$ . bin/activate
(venv) $ pip install cookiecutter
Collecting cookiecutter
...
```

Then simply run [Cookiecutter] where you want to create the new project. A new
directory will be created with the generated project name. For example:

```sh
cd ~/devel
cookiecutter gh:frequenz-floss/frequenz-repo-config-python --directory=cookiecutter
```

This command will prompt you for the project type, name, and other
configuration options, and it will generate the entire project for you.

It is recommended to use a released version, you can do that by adding the
option `--checkout <version>` to the command above. You can check which is the
latest version
[here](https://github.com/frequenz-floss/frequenz-repo-config-python/releases/latest).

After completing the project and fixing the `TODO`s, you can either amend the
previous commit using `git commit --amend` or create a new commit for the
changes using `git commit`.

## Documentation

For more detailed documentation, please check the [project's
website](https://frequenz-floss.github.io/frequenz-repo-config-python/).

## Contributing

If you want to know how to build this project and contribute to it, please
refer to the [Contributing Guide](CONTRIBUTING.md).


[Cookiecutter]: https://cookiecutter.readthedocs.io/en/stable
