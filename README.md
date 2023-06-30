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

After completing it and fixing the `TODO`s you can amend the previous commit
using `git commit --amend` or create a new commit for the changes using `git
commit`.

### Create the local development environment

To start the development, you need to make sure your environment is correctly
setup. One way to do this is by using a virtual environment and installing all
the dependencies there:

```sh
# requires at least python version 3.11
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

This will install you package in [*editable*
mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html), so
you can open a python interpreter and import your package modules and pick up
any local changes without the need to reinstall.  You can now run tools
directly, like `pytest`.

### Verify the new repository is healthy using `nox`

If you prefer to keep your virtual enviroment cleaner and avoid installing development dependencies, you can also use `nox` to create isolated environments for you:

```sh
pip install -e .[dev-noxfile]
nox --install-only  # Set up virtual environments once
nox -R  # Run linting and testing reusing the already existing virtual environments
```

This will only install you package in *editable* mode and the minimum
dependencies to be able to run `nox`, and then run all `nox` default sessions,
which will run linters and tests.

!!! note

    It's much faster to use `nox` with `--install-only` once (each time to
    change or update dependencies you need to run it again) and then using `nox
    -R` to run the sessions without re-creating the virtual environments.

    Otherwise `nox` will create many virtual environments each time you run it,
    which is **very** slow.

### Verify the generated documentation works

To generate the documentation you can use `mkdocs`:

```sh
pip install .[dev-mkdocs]  # Not necessary if you already installed .[dev]
mkdocs serve
```

If the command fails, look at the log warnings and errors and fix them.  If it
worked, now there is a local web server serving the documentation, you can
point your browser to Now you can point your browser to
[http://127.0.0.1:8000](/http://127.0.0.1:8000/) to have a look.

!!! info

    For API projects `docker` is needed to generate and serve documentation, as
    the easiest way to use the [tool to generate the documentation from
    `.proto`](https://github.com/pseudomuto/protoc-gen-doc) files is using
    `docker`.

### Initialize the GitHub pages website

The generated documentation can be easily published via GitHub pages, and it
will be automatically updated for new pushed and releases, but for that to work
correctly, some initial setup is needed:

```sh
pip install -e .[dev-mkdocs]  # Not necessary if you already installed .[dev]
mike deploy --update-aliases next latest  # Creates the branch gh-pages locally
mike set-default latest  # Makes the latest alias the default version
git push upstream gh-pages  # Pushes the new branch upstream so the website is published
```

Then make sure that GitHub pages is enabled in
`https://github.com/<repo-owner>/<repo-name>/settings/pages`.

If all went well, your website should be available soon via
`https://<repo-owner>.github.io//<repo-name>/`.

## Migrate an existing project

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
rsync -vr --exclude=.git/ new-project/ /path/to/existing/project
cd /path/to/existing/project
git diff
# Fix all the `TODO`s and cleanup the generated files
git commit -a
```

!!! warning

    The trailing slash in `new-project/` and the lack of it in
    `/path/to/existing/project` are meaningful to `rsync`.

    Also make sure to **exclude** the `.git/` directory to avoid messing up
    with your local git repository.

!!! tip

    Please have a look at the follow-up steps listed in the [Start a new
    project](#create-the-local-development-environment) section to finish the
    setup.

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

!!! tip

    Please have a look at the follow-up steps listed in the [Start a new
    project](#create-the-local-development-environment) section to finish the
    setup.

## Advanced usage

The Cookiecutter template uses some tools provided as a library by this
project.

Usually users don't need deal with it directly, but if you project needs some
extra customization (like disabling `nox` sessions or adding new ones, or using
different CLI options for some tools), then you'll need to.

You can find information about the extra features in the [API
refence](reference/frequenz/repo/config/).

## Contributing

If you want to know how to build this project and contribute to it, please
check out the [Contributing Guide](CONTRIBUTING.md).
