# Frequenz repository common configuration for Python

This is very opinionated set of tools and configurations to setup a Python
repository for Frequenz projects.

If offers:

* [Cookiecutter] templates for scaffolding new projects
* Trivial build of `noxfile.py` with some predefined sessions with all common
  checks.
* Tools to build protobuf/grpc files as Python, including type information.


[Cookiecutter]: https://cookiecutter.readthedocs.io/en/stable

## Start a new project

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

After completing it and fixing the TODOs
you can amend the previous commit using `git commit --amend`
or create a new commit for the changes using `git commit`.
You can make sure linting and tests pass by creating a virtual
environment, installing the development dependencies and running `nox`:
```sh
# requires at least python version 3.11
python3 -m venv .venv
. .venv/bin/activate
pip install .[dev-noxfile]
nox
```
