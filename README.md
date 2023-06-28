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

## Migrating an existing project

The easiest way to migrate an existing project is to just generate a new one
basing all the inputs in the current project metadata and then overwritting the
existing files.

It is recommended to commit all changes before doing this, so you can then use
`git` to look at the changes.

If you generate the new repo in a temporary directory, you can easily overwrite
the files in your existing project by using `rsync` or similar tools:

```sh
cd /tmp
cookiecutter gh:frequenz-floss/frequenz-repo-config-python --directory=cookiecutter
rsync -r new-project/ /path/to/existing/project
cd /path/to/existing/project
git diff
# Fix all the `TODO`s and cleanup the generated files
git commit -a
```

!!! warning

    The trailing slash in `new-project/` and the lack of it in
    `/path/to/existing/project` are meaningful to `rsync`.

## Update an existing project

To update an existing project you can use the [Cookiecutter *replay
file*](https://cookiecutter.readthedocs.io/en/stable/advanced/replay.html) that
was saved during the project generation.  The file is saved in
`.cookiecutter-replay.json`.  Using this file you can re-run Cookiecutter
without having to enter all the inputs again.

!!! warning

    Don't forget to commit all changes in your repository before doing this!
    Files will be overwritten!

```sh
git commit -a  # commit all changes
cd ..
cookiecutter gh:frequenz-floss/frequenz-repo-config-python \
    --directory=cookiecutter \
    --force \
    --replay \
    --replay-file project-directory/.cookiecutter-replay.json
```

This will create a new commit with all the changes to the overwritten files.
Bear in mind that all the `TODO`s will come back, so there will be quite a bit
of cleanup to do.  You can easily check what was changed using `git show`, and
you can use `git commit --amend` to amend the previous commit with the template
updates, or create a new commit with the fixes.  You can also use `git citool`
or `git gui` to easily add, remove or even discard (revert) changes in the
templates update commit.

!!! note

    The `project-directory` is the directory of your previously generated
    project. If you renamed it, then the files will be generated in a new
    directory with the original name.  You can update the target directory in
    the replay file.

!!! note

    Please remember to keep your replay file up to date if you change any
    metadata in the project.

## Contributing

If you want to know how to build this project and contribute to it, please
check out the [Contributing Guide](CONTRIBUTING.md).
