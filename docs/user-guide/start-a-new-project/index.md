# Starting a new project

## Install Cookiecutter

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
[cookiecutter] $ pip install cookiecutter
Collecting cookiecutter
...
```

Then simply run [Cookiecutter] where you want to create the new project:

## Generate the project files

```sh
cookiecutter gh:frequenz-floss/frequenz-repo-config-python \
    --directory=cookiecutter{{" --checkout " + version.ref_name if version}}
```

This command will prompt you for the project type, name, and other
configuration options, and it will generate the entire project for you in a new
subdirectory.

!!! Warning

    This command needs to be typed literally!

    `frequenz-floss/frequenz-repo-config-python` is the GitHub repository with
    the cookiecutter template that will be downloaded, and
    `--directory=cookiecutter` is needed because the cookiecutter template
    doesn't live at the top-level of that repository, but in a subdirectory
    called `cookiecutter`.{{" The `--checkout` option is provided to use
    a template from a released version, otherwise the default (development)
    branch will be used." if version}}

    All information about your project will be prompted interactively by that
    command.

After completing the project and fixing the `TODO`s, you can either amend the
previous commit using `git commit --amend` or create a new commit for the
changes using `git commit`.

### Template variables reference

--8<-- "cookiecutter/variable-reference.md"

## Create the local environment

To start development, you need to make sure your environment is correctly set
up. One way to do this is by using a virtual environment and installing all the
dependencies there:

```sh
# requires at least Python version 3.11
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

This will install your package in [*editable*
mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html), so
you can open a Python interpreter and import your package modules, picking up
any local changes without the need to reinstall. Now you can run tools
directly, like `pytest`.

## Verify using `nox`

If you prefer to keep your virtual environment cleaner and avoid installing
development dependencies, you can also use `nox` to create isolated
environments:

```sh
pip install -e .[dev-noxfile]
nox --install-only  # Set up virtual environments once
nox -R  # Run linting and testing reusing the existing virtual environments
```

This will only install your package in *editable* mode and the minimum
dependencies required to run `nox`. It will then run all `nox` default
sessions, which include running linters and tests.

!!! Tip

    It's much faster to use `nox` with `--install-only` once (each time you
    change or update dependencies, you need to run it again) and then use `nox
    -R` to run the sessions without recreating the virtual environments.

    Otherwise, `nox` will create many virtual environments each time you run
    it, which is **very** slow.

## Verify the documentation works

To generate the documentation, you can use `mkdocs`:

```sh
pip install .[dev-mkdocs]  # Not necessary if you already installed .[dev]
mkdocs serve
```

If the command fails, look at the log warnings and errors and fix them. If it
worked, now there is a local web server serving the documentation. You can
point your browser to [http://127.0.0.1:8000](http://127.0.0.1:8000) to have
a look.

!!! Info

    For API projects, `docker` is needed to generate and serve documentation,
    as the easiest way to use the [tool to generate the documentation from
    `.proto` files](https://github.com/pseudomuto/protoc-gen-doc) is using
    `docker`.

## Initialize GitHub Pages

The generated documentation can be easily published via GitHub Pages, and it
will be automatically updated for new pushes and releases. However, some
initial setup is needed for it to work correctly:

```sh
pip install -e .[dev-mkdocs]  # Not necessary if you already installed .[dev]
# Creates the branch gh-pages locally
mike deploy --update-aliases v0.1-dev v0-dev latest-dev latest
mike set-default latest  # Makes the latest alias the default version
git push upstream gh-pages  # Pushes the new branch upstream to publish the website
```

This assumes your branch is called `v0.x.x` and your first release will be `v0.1.0`.

Then make sure that GitHub Pages is enabled in
`https://github.com/<repo-owner>/<repo-name>/settings/pages`.

If all went well, your website should be available soon via
`https://<repo-owner>.github.io/<repo-name>/`.

### Versions using Mike

The above commands create a new documentation version using
[Mike](https://pypi.org/project/mike/), which is used to keep multiple versions
of the website.

The new documentation version is called `v0.1-dev`, which is used as the name
for the currently in-development branch. The `v0.1-dev` branch has an alias
called `v0-dev` that points to the latest v0.x branch development version, an
alias `latest-dev` that points to the latest in-development version, and
a `latest` alias, which is set as the *default*.

If the website is visited without specifying an explicit version, the `latest`
version will be displayed. It is recommended to point `latest` to the latest
stable version instead of the currently in-devepoment version, so as soon as
you make a release, you should update the alias.

### Automatic generation

New versions of the documentation will be automatically generated and published
via GitHub Actions on any push.

If a push is to a branch with semver-like format (vX.Y.Z), then the generated
version will replace the current `vX.Y-dev` version (and `vX-dev` and
`latest-dev` alias).

If a tag is pushed instead, then the generated version will replace the current
`vX.Y` version (if there was any), and the aliases `vX` and `latest` will be
updated to point to the new version.

To summarize, we don't create versions for patch releases, only for minor
versions, and we have an alias to point to the latest version of a major
version too.
