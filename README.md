# Frequenz repository common configuration for Python

[![Build Status](https://github.com/frequenz-floss/frequenz-repo-config-python/actions/workflows/ci.yaml/badge.svg)](https://github.com/frequenz-floss/frequenz-repo-config-python/actions/workflows/ci.yaml)
[![PyPI Package](https://img.shields.io/pypi/v/frequenz-repo-config)](https://pypi.org/project/frequenz-repo-config/)
[![Docs](https://img.shields.io/badge/docs-latest-informational)](https://frequenz-floss.github.io/frequenz-repo-config-python/)

## Introduction

This is very opinionated set of tools and configurations to setup a Python
repository for [Frequenz](https://frequenz.com) projects.

If offers:

* [Cookiecutter] templates for scaffolding new projects
* Trivial build of `noxfile.py` with some predefined sessions with all common
  checks.
* Tools to build protobuf/grpc files as Python, including type information.

## Quick Example

To start a new project you should first [install
Cookiecutter](https://cookiecutter.readthedocs.io/en/stable/installation.html).
It is normally available in any Linux distribution, but some have a very old
version (for example, Ubuntu/Debian).  You can [check which version your distro
has in Repology](https://repology.org/project/cookiecutter/versions). You need
**at least version 2.1.0**.  To make sure to get an up to date version you can
always uses `pip` and install in a `venv`:

```console
$ python -m venv cookiecutter
$ cd cookiecutter
$ . bin/activate
[cookiecutter] $ pip install cookiecutter
Collecting cookiecutter
...
```

Then just run cookiecutter where you want to create the new project. A new
directory will be created with the generated project name. For example:

```sh
cd ~/devel
cookiecutter gh:frequenz-floss/frequenz-repo-config-python --directory=cookiecutter
```

This will prompt for the project type, name and other configuration and
generate the whole project for you.

After completing it and fixing the `TODO`s you can amend the previous commit
using `git commit --amend` or create a new commit for the changes using `git
commit`.

## Documentation

For more detailed documentation please check the [project's
website](https://frequenz-floss.github.io/frequenz-repo-config-python/).

## Contributing

If you want to know how to build this project and contribute to it, please
check out the [Contributing Guide](CONTRIBUTING.md).


[Cookiecutter]: https://cookiecutter.readthedocs.io/en/stable
