* `type`: The type of repository. It must be chosen from the list.

* `name`: The name of the project. This will be used to build defaults for
  other inputs, such as `title`, `python_package`, etc. It should be one word,
  using only alphanumeric characters (and starting with a letter).

* `description`: A short description of the project. It will be used as the
  description in the `README.md`, `pyproject.toml`, `mkdocs.yml`, etc.

* `title`: A human-readable name or title for the project. It will be used in
  the `README.md`, `CONTRIBUTING.md`, and other files to refer to the project,
  as well as the site title in `mkdocs.yml`.

* `keywords`: A comma-separated list of keywords that will be used in the
  `pyproject.toml` file. If left untouched, it will use only some predefined
  keywords. If anything else is entered, it will be **added** to the default
  keywords.

* `github_org`: The GitHub handle of the organization where the project will
  reside. This will be used to generate links to the project on GitHub.

* `license`: Currently, only two options are provided: `MIT`, which should be
  used for open-source projects, and `Proprietary`, which should be used for
  closed-source projects. This will be added to file headers and used as the
  license in `pyproject.toml`.

* `author_name`, `author_email`: The name and email address of the author of
  the project. They will be used in the copyright notice in file headers and
  as the author in `pyproject.toml`.

* `python_package`: The Python package in which this project will reside. All
  files provided by this project should be located in this package. This needs
  to be a list of valid Python identifiers separated by dots. The source file
  structure will be derived from this. For example, `frequenz.actor.example`
  will generate files in `src/frequenz/actor/example`.

* `pypi_package_name`: The name of the PyPI/wheel/distribution package. This
  should be consistent with the `python_package`, usually replacing `.` with
  `-`. For example, `frequenz-actor-example`.

* `github_repo_name`: The handle of the GitHub repository where the project
  will reside. This will be used to generate links to the project on GitHub and
  as the top-level directory name.

* `default_codeowners`: A space-separated list of GitHub teams (`@org/team`) or
  users (`@user`) that will be the default code owners for this project. This
  will be used to build the `CODEOWNERS` file. Please refer to the [code owners
  documentation] for more details on the valid syntax.

[code owners documentation]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
