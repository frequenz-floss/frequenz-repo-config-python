# Frequenz Repository Configuration Release Notes

## Summary

This release adds linting of code examples in *docstrings*, a workflow to check if PRs have updated the release notes and an [editorconfig](https://editorconfig.org/) file, as well as a bunch of bug fixes.

## Upgrading

- nox: Now the default configuration for API repositories will not automatically add `pytests` as an `extra_path`

  The `pytests` directory is not a standard directory that will be auto-discovered by `pytest`, so it should always be included in the `pyproject.toml` file, in the `tool.pytest.ini_options.testpaths` array. Please check your API project is properly configured.

### Cookiecutter template

- To make the new workflow to check if release notes were updated you should add the check to the branch protection rules of your repository to require this check to pass. You should also add a new label *"cmd:skip-release-notes"* to be able to override the check. You can use the following script to do it:

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

## New Features

- Add support for linting code examples found in *docstrings*.

  A new module `frequenz.repo.config.pytest.examples` is added with an utility function to be able to easily collect and lint code examples in *docstrings*.

  There is also a new optional dependency `extra-lint-examples` to easily pull the dependencies needed to do this linting. Please have a look at the documentation in the `frequenz.repo.config` package for more details.

### Cookiecutter template

- Add a new GitHub workflow to check that release notes were updated.

  This workflow will check PRs to see if a change was done in the `src/` directory, and if so, it will fail if the `RELEASE_NOTES.md` wasn't also updated.

  Users can override this by assigning the label `cmd:skip-release-notes` to the PR for changes that don't really need a release notes update.

- Add `MANIFEST.in` file.

  This makes sure that we don't ship useless files when building the distribution package and that we include all the relevant files too, like generated *.pyi files for API repositories.

- Add an `.editorconfig` file to ensure a common basic editor configuration for different file types.

- Add a `pytest` hook to collect and lint code examples found in *docstrings* using `pylint`.

  Examples found in code *docstrings* in the `src/` directory will now be collected and checked using `pylint`. This is done via the file `src/conftest.py`, which hooks into `pytest`, so to only check the examples you can run `pylint src`.

  !!! info

      There is a bug in the library used to extract the examples that prevents from collecting examples from `__init__.py` files. See https://github.com/frequenz-floss/frequenz-repo-config-python/issues/113 for more details.

## Bug Fixes

- The distribution package doesn't include tests and other useless files anymore.

- nox

  * When discovering path *extra paths*, now paths will not be added if they are also *source paths*, as we don't want any duplicates.

  * Fix copying of `Config` and `CommandOptions` objects.

### Cookiecutter template

- Now the CI workflow will checkout the submodules.

- Fix adding of an empty keyword.

- Don't distribute development files in the source distribution.
