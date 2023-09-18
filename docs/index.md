# Frequenz Repository Configuration

## Introduction

This is a highly opinionated set of tools and configurations to set up a Python
repository for [Frequenz](https://frequenz.com) projects.

It offers:

* [Cookiecutter] templates for scaffolding new projects
* Trivial build of `noxfile.py` with some predefined sessions that include all
  common checks.
* Tools to build protobuf/grpc files as Python, including type information.

## Start a new project

To start a new project, you should first [install
Cookiecutter](https://cookiecutter.readthedocs.io/en/stable/installation.html).
It is normally available in any Linux distribution, but some have a very old
version (for example, Ubuntu/Debian). You can [check which version your distro
has on Repology](https://repology.org/project/cookiecutter/versions). You need
**at least version 2.1.0**. To ensure you get an up-to-date version, you can
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

```sh
cookiecutter gh:frequenz-floss/frequenz-repo-config-python \
    --directory=cookiecutter --checkout v0.6.2
```

This command will prompt you for the project type, name, and other
configuration options, and it will generate the entire project for you in a new
subdirectory.

!!! warning

    This command needs to be typed literally!

    `frequenz-floss/frequenz-repo-config-python` is the GitHub repository with
    the cookiecutter template that will be downloaded, and
    `--directory=cookiecutter` is needed because the cookiecutter template
    doesn't live at the top-level of that repository, but in a subdirectory
    called `cookiecutter`. The `--checkout` option is provided to use
    a template from a released version, otherwise the default (development)
    branch will be used.

    All information about your project will be prompted interactively by that
    command.

After completing the project and fixing the `TODO`s, you can either amend the
previous commit using `git commit --amend` or create a new commit for the
changes using `git commit`.

### Template variables reference

--8<-- "cookiecutter/variable-reference.md"

### Create the local development environment

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

### Verify the new repository is healthy using `nox`

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

!!! note

    It's much faster to use `nox` with `--install-only` once (each time you
    change or update dependencies, you need to run it again) and then use `nox
    -R` to run the sessions without recreating the virtual environments.

    Otherwise, `nox` will create many virtual environments each time you run
    it, which is **very** slow.

### Configure the release notes check GitHub workflow

By default a workflow to check if the release notes were updated is
included. This workflow will check PRs to see if a change was done in the
`src/` directory, and if so, it will fail if the `RELEASE_NOTES.md` wasn't also
updated.

But this check will not be enforced unless some extra configuration is done. To
enforce the check for PRs to be merged you need to go to the *GitHub repository
-> Settings -> Branches* and select the rule for the branch you want to protect.

Then in the rules search for the *Require status checks to pass before merging*
checkbox and search for *"Check release notes are updated"* in the search box.

As sometimes it is OK for PRs not to have release notes, as maybe some changes
don't impact the end user, this workflow can be overridden by assigning the
label `cmd:skip-release-notes` to the PR. To be able to do this, you also need
to add that label to the repository.

You can do this from the GitHub web interface, or using one of the following
commands:

```sh
repo=...  # org/repo
token=... # GitHub token with the correct permissions
name="cmd:skip-release-notes"
desc="It is not necessary to update release notes for this PR"
color="930F79"

# Using cURL
curl -L \
    -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $token" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -d '{"name":"'"$name"'","description":"'"$desc"'","color":"'"$color"'"}' \
    "https://api.github.com/repos/$repo/labels"

# Using the gh tool (no need for a token if you already have it configured)
gh api -X POST \
    -f name="$name" -f description="$desc" -f color="$color" \
    "repos/$repo/labels"
```

### Verify the generated documentation works

To generate the documentation, you can use `mkdocs`:

```sh
pip install .[dev-mkdocs]  # Not necessary if you already installed .[dev]
mkdocs serve
```

If the command fails, look at the log warnings and errors and fix them. If it
worked, now there is a local web server serving the documentation. You can
point your browser to [http://127.0.0.1:8000](http://127.0.0.1:8000) to have
a look.

!!! info

    For API projects, `docker` is needed to generate and serve documentation,
    as the easiest way to use the [tool to generate the documentation from
    `.proto` files](https://github.com/pseudomuto/protoc-gen-doc) is using
    `docker`.

### Initialize the GitHub Pages website

The generated documentation can be easily published via GitHub Pages, and it
will be automatically updated for new pushes and releases. However, some
initial setup is needed for it to work correctly:

```sh
pip install -e .[dev-mkdocs]  # Not necessary if you already installed .[dev]
mike deploy --update-aliases next latest  # Creates the branch gh-pages locally
mike set-default latest  # Makes the latest alias the default version
git push upstream gh-pages  # Pushes the new branch upstream to publish the website
```

Then make sure that GitHub Pages is enabled in
`https://github.com/<repo-owner>/<repo-name>/settings/pages`.

If all went well, your website should be available soon via
`https://<repo-owner>.github.io/<repo-name>/`.

#### Website versions using Mike

The above commands create a new documentation version using
[Mike](https://pypi.org/project/mike/), which is used to keep multiple versions
of the website.

The new documentation version is called `next`, which is used as the name for
the currently in-development branch. The `next` branch has an alias called
`latest`, which is set as the *default*.

If the website is visited without specifying an explicit version, the `latest`
version will be displayed. It is recommended to point `latest` to the latest
stable version instead of the currently in-devepoment version, so as soon as
you make a release, you should update the alias.

#### Auto-generation of pages via GitHub Actions

New versions of the documentation will be automatically generated and published
via GitHub Actions on any push.

If a push is to a branch with semver-like format (vX.Y.Z), then the generated
version will replace the current `next` version.

If a tag is pushed instead, then the generated version will replace the current
`vX.Y` version (if there was any), and the aliases `vX` and `latest` will be
updated to point to the new version.

To summarize, we don't create versions for patch releases, only for minor
versions, and we have an alias to point to the latest version of a major
version too.

## Migrate an existing project

The easiest way to migrate an existing project is to generate a new one based
on the current project metadata and then overwrite the existing files.

It is recommended to commit all changes before doing this, so you can then use
`git` to look at the changes.

If you generate the new repo in a temporary directory, you can easily overwrite
the files in your existing project by using `rsync` or similar tools:

```sh
cd /tmp
cookiecutter gh:frequenz-floss/frequenz-repo-config-python \
    --directory=cookiecutter --checkout v0.6.2
rsync -vr --exclude=.git/ new-project/ /path/to/existing/project
cd /path/to/existing/project
git diff
# Fix all the `TODO`s and clean up the generated files
git commit -a
```

!!! warning

    The trailing slash in `new-project/` and the lack of it in
    `/path/to/existing/project` are meaningful to `rsync`.

    Also, make sure to **exclude** the `.git/` directory to avoid messing up
    with your local Git repository.

!!! tip

    Please have a look at the follow-up steps listed in the [Start a new
    project](#create-the-local-development-environment) section to finish the
    setup.

## Update an existing project

To update an existing project, you can use the [Cookiecutter *replay
file*](https://cookiecutter.readthedocs.io/en/stable/advanced/replay.html) that
was saved during the project generation. The file is saved as
`.cookiecutter-replay.json`. Using this file, you can re-run [Cookiecutter]
without having to enter all the inputs again.

!!! warning

    * Don't forget to commit all changes in your repository before doing this!
      Files will be overwritten!
    * Don't forget to check all the [release
      notes](https://github.com/frequenz-floss/frequenz-repo-config-python/releases)
      for all the versions you are going to update, in particular the
      **Upgrading** section, as there might be steps necessary before even
      running the `cookiecutter` command for the update.

```sh
git commit -a  # commit all changes
cd ..
cookiecutter gh:frequenz-floss/frequenz-repo-config-python \
    --directory=cookiecutter \
    --checkout v0.6.2 \
    --overwrite-if-exists \
    --replay \
    --replay-file project-directory/.cookiecutter-replay.json
```

This will create a new commit with all the changes to the overwritten files.
Bear in mind that all the `TODO`s will come back, so there will be quite a bit
of cleanup to do. You can easily check what was changed using `git show`, and
you can use `git commit --amend` to amend the previous commit with the template
updates, or create a new commit with the fixes. You can also use `git citool`
or `git gui` to easily add, remove, or even discard (revert) changes in the
templates update commit.

!!! note

    The `project-directory` is the directory of your previously generated
    project. If you renamed it, then the files will be generated in a new
    directory with the original name. You can update the target directory in
    the replay file.

!!! note

    Please remember to keep your replay file up to date if you change any
    metadata in the project.

!!! tip

    Please have a look at the follow-up steps listed in the [Start a new
    project](#create-the-local-development-environment) section to finish the
    setup.

## Advanced usage

The [Cookiecutter] template uses some tools provided as a library by this
project.

Usually, users don't need to deal with it directly, but if your project needs
some extra customization (like disabling `nox` sessions or adding new ones, or
using different CLI options for some tools), then you'll need to.

You can find information about the extra features in the [API
reference](reference/frequenz/repo/config/).


[Cookiecutter]: https://cookiecutter.readthedocs.io/en/stable
