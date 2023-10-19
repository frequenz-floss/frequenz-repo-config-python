# Frequenz Repository Configuration Release Notes

## Summary

This release focuses on improving the documentation generation and the CI. In particular it brings a new versioning scheme for the documentation that supports multiple development branches and exposes pre-releases.

## Upgrading

### Cookiecutter template

- The recommended `cookiecutter` version was bumped to 2.4.0 to avoid some buggy old versions.

- `mkdocs`

  - The script `docs/mkdocstrings_autoapi.py` was moved to `docs/_scripts/mkdocstrings.py`.
  - Note that now code annotations will be numbered. This is useful to hint about the order one should read the annotations.
  - The following files were renamed to keep the documentation directory clean for documentation files:

    - `docs/css` -> `docs/_css`
    - `docs/overrides` -> `docs/_overrides`
    - `logo.png` -> `docs/_img/logo.png`

  - You might need to remove old `mike` version aliases. Probably removing `next` should be enough:

    ```bash
    mike delete -p next
    ```

    You can use `mike list` to list all versions and aliases.

- CI

  - You can now make your branch protection rule only require the "Test with nox" CI job to pass. All the matrix expansions will merge into it, so there is no need to change branch protection rules if matrix elements are added or removed.
  - Dependabot now will check for updates monthly and on a random day and time.

- The `src/conftest.py` file was moved to `src/<project_path>/conftest.py`.

  This is to leave the `src` directory free of any files, so it is easier to navigate using auto-completion and GitHub file browser.

## New Features

- `frequenz_repo_config.version`: New module to get the version information for a repository.
- `frequnz_repo_config.github`: New module to interact with GitHub.
- `frequenz.repo_config.mkdocs.mike`: New module to manage `mike` versions and aliases.
- `frequenz.repo_config.cli`: New package to implement CLI commands.

  - `frequenz.repo.config.cli.version.mike.info`: New command to print GitHub Action variables with for the current `mike` version.
  - `frequenz.repo.config.cli.version.mike.sort`: New command to sort `mike` versions file (`versions.json`).

### Cookiecutter template

- `mkdocs`

  - New markdown extensions: [`def_list` / `task_list`](https://squidfunk.github.io/mkdocs-material/reference/lists/) and [`footnotes`](https://squidfunk.github.io/mkdocs-material/reference/footnotes/).
  - New [`mkdocs-macros`](https://mkdocs-macros-plugin.readthedocs.io/en/latest/) extension.
  - Show inherited attributes in the documentation.
  - Make code annotations numbered. This is useful to hint about the order one should read the annotations.
  - Add a navigation footer to show previous and next pages. This is specially useful when reading the documentation in a mobile device since the navigation bar is hidden.
  - Updated dependencies.
  - The hooking of `mkdocstrings` to `macros` plugins is moved to a separate function to avoid the noise in the `define_env()` function.
  - Improve formatting of signatures to show the types.
  - We use a new `mike` versioning scheme:

    - Versions now have a title with the full tag name for tags and includes the (short) commit SHA for branches so users can know exactly which version they are reading.
    - Pre-releases are now published too as `vX.Y-pre`. They have aliases to point to the latest pre-release in a major (`vX-pre`) and the absolute latest pre-release (`latest-pre`).
    - All branches are now published with their own version as `vX.Y-dev`. They have aliases to point to the latest version in a major (`vX-dev`) and the absolute latest version (`latest-dev`). This means the old `next` becomes `latest-dev`.

- CI

  - Add CI job to test package installation on multiple platforms (amd64 and arm64).
  - Add CI job to run the tests in arm64.
  - Add a CI job to *join* all `nox` runs, so only one branch protection rule needs to be used.
  - Dependabot now will check for updates monthly and on a random day and time. This is to avoid all repositories updating at the same time.

- Add a section about cross-arch testing to `CONTRIBUTING.md`.

## Bug Fixes

### Cookiecutter template

- `mkdocs`

  - Fixed mermaid diagrams not rendering in the documentation.
  - `mypy` ignores for `cookiecutter` have been removed. They should have never be there as generated projects don't use `cookiecutter`.
  - `mypy` overrides now are applied to API projects too.
  - Now the `latest` `mike` version will point to the highest stable version available, not the latest version published.

- Dependabot branches are now not tested for `push` events, as they are already tested by `pull` events.
