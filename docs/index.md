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

!!! Tip

    It's much faster to use `nox` with `--install-only` once (each time you
    change or update dependencies, you need to run it again) and then use `nox
    -R` to run the sessions without recreating the virtual environments.

    Otherwise, `nox` will create many virtual environments each time you run
    it, which is **very** slow.

### Configure the GitHub repository

The generated templates make some assumptions about how the GitHub repository
is configured. Here is a summary of changes you should do to the repository
to make sure everything works as expected.

#### Issues

##### Labels

Review the list of labels and add:

* `part:xxx` labels that make sense to the project

* Add a `cmd:skip-release-notes` with the following description:

    > It is not necessary to update release notes for this PR

    And `930F79` as color.

* All labels used by automation in the project, for example look for labels listed in:

    * `.github/keylabeler.yml`
    * `.github/labeler.yml`
    * `.github/dependabot.yml`
    * `.github/workflows/release-notes-check.yml`

#### Discussions

This depends on the repo, but in general we want this:

* Remove the *Show and tell* and *Poll* categories

* Rename the *Q&A* category to *Support* and change the emoji to :sos:

  This one is important to match the link provided in `.github/ISSUE_TEMPLATE/config.yml`.

#### Settings

##### General

###### Default branch

* Rename to `v0.x.x` (this is required for the common CI to work properly when creating releases)

###### Features

- [ ] Wikis
- [x] Issues
- [ ] Sponsorships
- [x] Projects
- [x] Preserve this repository
- [x] Discussions

###### Pull Requests

- [x] Allow merge commits: Default to pull request title and description
- [ ] Allow squash merging
- [ ] Allow rebase merging
- [ ] Always suggest updating pull request branches
- [x] Allow auto-merge
- [x] Automatically delete head branches

###### Archives

- [ ] Include Git LFS objects in archives

###### Pushes

- [x] Limit how many branches and tags can be updated in a single push: 5

##### Collaborators and teams

* Give the team owning the repository *Role: Admin*
* Give *everybody* team *Role: Triage*

##### Branches

After importing code to the repository, add the following *Branch protection
rules* (as always this is a guideline, defaults that should be used unless
there is a reason to diverge):

###### Protect matching branches

!!! Note inline end

    This is only to enable the merge queue, all the real protection rules will
    be added afterwards via [rulesets](#rulesets). This is why all other
    protections are disabled here.

Add a rule for the **main branch** (`v0.x.x`) without wildcards so merge queues
can be enabled:

- [ ] Require a pull request before merging
    - [ ] Require approvals: 1
    - [ ] Dismiss stale pull request approvals when new commits are pushed
    - [ ] Require review from Code Owners
    - [ ] Restrict who can dismiss pull request reviews
    - [ ] Allow specified actors to bypass required pull requests
    - [ ] Require approval of the most recent reviewable push
- [ ] Require status checks to pass before merging
    - [ ] Require branches to be up to date before merging
    - **(add all the tests that should pass)**
- [ ] Require conversation resolution before merging
- [ ] Require signed commits
- [ ] Require linear history
- [x] Require merge queue:
    * Maximum pull requests to build: **5**
    * Minimum pull requests to merge: **2** (this should be the only change
      to defaults) or after **5** minutes
    * Maximum pull requests to merge: **5**
    - [x] Only merge non-failing pull requests
    * Consider check failed after **60**
- [ ] Require deployments to succeed before merging
- [ ] Lock branch
- [ ] Do not allow bypassing the above settings
- [ ] Restrict who can push to matching branches (this might be disabled
  while pushing the initial changes)
- Rules applied to everyone including administrators
    - [ ] Allow force pushes
    - [ ] Allow deletions

##### Rules

###### Rulesets

![Importing rulesets](_img/import-rulesets.png)

Import the following
[rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets):

!!! Note inline end

    You might need to adapt the status checks in the *Protect version
    branches* ruleset depending on your repository configuration.

{% set ref_name = version.ref_name if version else default_branch %}

* [Disable creation of non-release
  tags]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Disable.creation.of.non-release.tags.json)
* [Disable creation of other
  branches]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Disable.creation.of.other.branches.json)
* [Disallow removal and force-pushes of
  gh-pages]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Disallow.removal.and.force-pushes.of.gh-pages.json)
* [Protect released
  tags]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Protect.released.tags.json)
* [Protect version
  branches]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Protect.version.branches.json)

##### Code security and analysis

* Enable *Dependabot version updates* if relevant

#### Code

The basic code configuration should be generate using
[repo-config](https://frequenz-floss.github.io/frequenz-repo-config-python/).

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

!!! Info

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
mike deploy --update-aliases v0.1-dev latest-dev latest # Creates the branch gh-pages locally
mike set-default latest  # Makes the latest alias the default version
git push upstream gh-pages  # Pushes the new branch upstream to publish the website
```

This assumes your branch is called `v0.x.x` and your first release will be `v0.1.0`.

Then make sure that GitHub Pages is enabled in
`https://github.com/<repo-owner>/<repo-name>/settings/pages`.

If all went well, your website should be available soon via
`https://<repo-owner>.github.io/<repo-name>/`.

#### Website versions using Mike

The above commands create a new documentation version using
[Mike](https://pypi.org/project/mike/), which is used to keep multiple versions
of the website.

The new documentation version is called `v0.1-dev`, which is used as the name for
the currently in-development branch. The `v0.1-dev` branch has an alias called
`latest-dev` that points to the latest in-development version, and `latest`
alias, which is set as the *default*.

If the website is visited without specifying an explicit version, the `latest`
version will be displayed. It is recommended to point `latest` to the latest
stable version instead of the currently in-devepoment version, so as soon as
you make a release, you should update the alias.

#### Auto-generation of pages via GitHub Actions

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
    --directory=cookiecutter{{(" --checkout " + version.ref_name) if version}}
rsync -vr --exclude=.git/ new-project/ /path/to/existing/project
cd /path/to/existing/project
git diff
# Fix all the `TODO`s and clean up the generated files
git commit -a
```

!!! Warning

    The trailing slash in `new-project/` and the lack of it in
    `/path/to/existing/project` are meaningful to `rsync`.

    Also, make sure to **exclude** the `.git/` directory to avoid messing up
    with your local Git repository.

!!! Tip

    Please have a look at the follow-up steps listed in the [Start a new
    project](#create-the-local-development-environment) section to finish the
    setup.

## Update an existing project

To update an existing project, you can use the [Cookiecutter *replay
file*](https://cookiecutter.readthedocs.io/en/stable/advanced/replay.html) that
was saved during the project generation. The file is saved as
`.cookiecutter-replay.json`. Using this file, you can re-run [Cookiecutter]
without having to enter all the inputs again.

!!! Warning

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
    --directory=cookiecutter \{{ """
    --checkout """ + version.ref_name + " \\" if version}}
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

!!! Note

    The `project-directory` is the directory of your previously generated
    project. If you renamed it, then the files will be generated in a new
    directory with the original name. You can update the target directory in
    the replay file.

!!! Note

    Please remember to keep your replay file up to date if you change any
    metadata in the project.

!!! Tip

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
