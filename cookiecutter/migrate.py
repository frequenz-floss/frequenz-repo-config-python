#!/usr/bin/env python3
# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Script to migrate existing projects to new versions of the cookiecutter template.

This script migrates existing projects to new versions of the cookiecutter
template, removing the need to completely regenerate the project from
scratch.

To run it, the simplest way is to fetch it from GitHub and run it directly:

    curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/<tag>/cookiecutter/migrate.py | python3

Make sure to replace the `<tag>` to the version you want to migrate to in the URL.

For jumping multiple versions you should run the script multiple times, once
for each version.

And remember to follow any manual instructions for each run.
"""  # noqa: E501

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import SupportsIndex


def main() -> None:
    """Run the migration steps."""
    # Add a separation line like this one after each migration step.
    print("=" * 72)
    regroup_dependabot()
    print("=" * 72)
    use_new_workflows()
    print("=" * 72)
    print("Migration script finished. Remember to follow any manual instructions.")
    print("=" * 72)


# pylint: disable=too-many-lines


def regroup_dependabot() -> None:
    """Use new dependabot groups to separate dependencies that break often."""
    print("Using new dependabot groups to separate dependencies that break often...")
    # Dependabot configuration file
    dependabot_file = Path(".github/dependabot.yml")

    # Skip if the file doesn't exist
    if not dependabot_file.exists():
        manual_step(
            "Dependabot configuration file not found, not excluding "
            "frequenz-repo-config from group updates. Please consider adding a "
            "dependabot configuration file."
        )
        return

    dependabot_content = dependabot_file.read_text(encoding="utf-8")

    new_groups = """\
    # We group patch updates as they should always work.
    # We also group minor updates, as it works too for most libraries,
    # typically except libraries that don't have a stable release yet (v0.x.x
    # branch), so we make some exceptions for them.
    # Major updates and dependencies excluded by the above groups are still
    # managed, but they'll create one PR per dependency, as breakage is
    # expected, so it might need manual intervention.
    # Finally, we group some dependencies that are related to each other, and
    # usually need to be updated together.
    groups:
      patch:
        update-types:
          - "patch"
        exclude-patterns:
          # pydoclint has shipped breaking changes in patch updates often
          - "pydoclint"
      minor:
        update-types:
          - "minor"
        exclude-patterns:
          - "async-solipsism"
          - "frequenz-repo-config*"
          - "markdown-callouts"
          - "mkdocs-gen-files"
          - "mkdocs-literate-nav"
          - "mkdocstrings*"
          - "pydoclint"
          - "pytest-asyncio"
      # We group repo-config updates as it uses optional dependencies that are
      # considered different dependencies otherwise, and will create one PR for
      # each if we don't group them.
      repo-config:
        patterns:
          - "frequenz-repo-config*"
      mkdocstrings:
        patterns:
          - "mkdocstrings*"
"""

    marker = "    open-pull-requests-limit: 10"
    if marker not in dependabot_content:
        manual_step(
            f"Could not file marker ({marker!r}) in {dependabot_file}, "
            "can't update automatically. Please consider using these new groups "
            "in the dependabot configuration file:"
        )
        return

    text_to_replace = ""
    found_marker = False
    for line in dependabot_content.splitlines():
        if line == marker:
            found_marker = True
            continue
        if not found_marker:
            continue
        if line == "" and found_marker:
            break
        text_to_replace += line + "\n"

    if not text_to_replace:
        manual_step(
            "Could not find the text to replace with the new depenndabot "
            "groups. Please consider using these new groups in the dependabot "
            "configuration file:"
        )
        return

    replace_file_contents_atomically(
        dependabot_file,
        text_to_replace,
        new_groups,
        count=1,
        content=dependabot_content,
    )


def use_new_workflows() -> None:
    """Use the new GitHub Actions workflows."""
    print("Splitting the old GitHub ci.yaml workflow into ci.yaml and ci-pr.yaml...")
    try:
        os.unlink(".github/workflows/ci.yaml")
    except OSError as err:
        print(f"Failed to remove old ci.yaml: {err}", file=sys.stderr)

    project_type: str | None = None
    try:
        with open(".cookiecutter-replay.json", "r", encoding="utf-8") as json_file:
            cookiecutter_json = json.load(json_file)
        project_type = cookiecutter_json["cookiecutter"]["type"]
    except Exception as err:  # pylint: disable=broad-except
        print(f"Failed to load .cookiecutter-replay.json: {err}", file=sys.stderr)
        print("The project will be considered a regular project, not a API project")

    def print_todos(file_name: str, contents: str) -> None:
        for index, line in enumerate(contents.splitlines(), start=1):
            if "TODO(cookiecutter):" in line:
                print(f"  {file_name}:{index}: {line}")

    with open(".github/workflows/ci.yaml", "w", encoding="utf-8") as new_file:
        contents_ci = NEW_CI_API if project_type == "api" else NEW_CI
        new_file.write(contents_ci)

    with open(".github/workflows/ci-pr.yaml", "w", encoding="utf-8") as new_file:
        contents_pr = NEW_CI_PR_API if project_type == "api" else NEW_CI_PR
        new_file.write(contents_pr)

    manual_step(
        "The ci.yaml and ci-pr.yaml files have been created. Please review the "
        "changes and make sure they work for your project and remember to add the new "
        "ci-pr.yaml to git: git add .github/workflows/ci-pr.yaml. Please also check "
        "the new TODOs."
    )
    print_todos(".github/workflows/ci.yaml", contents_ci)
    print_todos(".github/workflows/ci-pr.yaml", contents_pr)


NEW_CI = r"""name: CI

on:
  merge_group:
  push:
    # We need to explicitly include tags because otherwise when adding
    # `branches-ignore` it will only trigger on branches.
    tags:
      - '*'
    branches-ignore:
      # Ignore pushes to merge queues.
      # We only want to test the merge commit (`merge_group` event), the hashes
      # in the push were already tested by the PR checks
      - 'gh-readonly-queue/**'
      - 'dependabot/**'
  workflow_dispatch:

env:
  # Please make sure this version is included in the `matrix`, as the
  # `matrix` section can't use `env`, so it must be entered manually
  DEFAULT_PYTHON_VERSION: '3.11'
  # It would be nice to be able to also define a DEFAULT_UBUNTU_VERSION
  # but sadly `env` can't be used either in `runs-on`.

jobs:
  nox:
    name: Test with nox
    strategy:
      fail-fast: false
      matrix:
        arch:
          - amd64
          - arm
        os:
          - ubuntu-24.04
        python:
          - "3.11"
          - "3.12"
        nox-session:
          # To speed things up a bit we use the special ci_checks_max session
          # that uses the same venv to run multiple linting sessions
          - "ci_checks_max"
          - "pytest_min"
    runs-on: ${{ matrix.os }}${{ matrix.arch != 'amd64' && format('-{0}', matrix.arch) || '' }}

    steps:
      - name: Run nox
        uses: frequenz-floss/gh-action-nox@v1.0.0
        with:
          python-version: ${{ matrix.python }}
          nox-session: ${{ matrix.nox-session }}
          # TODO(cookiecutter): Uncomment this for projects with private dependencies
          # git-username: ${{ secrets.GIT_USER }}
          # git-password: ${{ secrets.GIT_PASS }}

  # This job runs if all the `nox` matrix jobs ran and succeeded.
  # It is only used to have a single job that we can require in branch
  # protection rules, so we don't have to update the protection rules each time
  # we add or remove a job from the matrix.
  nox-all:
    # The job name should match the name of the `nox` job.
    name: Test with nox
    needs: ["nox"]
    # We skip this job only if nox was also skipped
    if: always() && needs.nox.result != 'skipped'
    runs-on: ubuntu-24.04
    env:
      DEPS_RESULT: ${{ needs.nox.result }}
    steps:
      - name: Check matrix job result
        run: test "$DEPS_RESULT" = "success"

  build:
    name: Build distribution packages
    # Since this is a pure Python package, we only need to build it once. If it
    # had any architecture specific code, we would need to build it for each
    # architecture.
    runs-on: ubuntu-24.04

    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Fetch sources
        uses: actions/checkout@v4
        with:
          submodules: true

      - name: Setup Python
        uses: frequenz-floss/gh-action-setup-python-with-deps@v1.0.0
        with:
          python-version: ${{ env.DEFAULT_PYTHON_VERSION }}
          dependencies: build

      - name: Build the source and binary distribution
        run: python -m build

      - name: Upload distribution files
        uses: actions/upload-artifact@v4
        with:
          name: dist-packages
          path: dist/
          if-no-files-found: error

  test-installation:
    name: Test package installation
    needs: ["build"]
    strategy:
      fail-fast: false
      matrix:
        arch:
          - amd64
          - arm
        os:
          - ubuntu-24.04
        python:
          - "3.11"
          - "3.12"
    runs-on: ${{ matrix.os }}${{ matrix.arch != 'amd64' && format('-{0}', matrix.arch) || '' }}

    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Print environment (debug)
        run: env

      - name: Download package
        uses: actions/download-artifact@v4
        with:
          name: dist-packages
          path: dist

      # This is necessary for the `pip` caching in the setup-python action to work
      - name: Fetch the pyproject.toml file for this action hash
        env:
          GH_TOKEN: ${{ github.token }}
          REPO: ${{ github.repository }}
          REF: ${{ github.sha }}
        run: |
          set -ux
          gh api \
              -X GET \
              -H "Accept: application/vnd.github.raw" \
              "/repos/$REPO/contents/pyproject.toml?ref=$REF" \
            > pyproject.toml

      - name: Setup Python
        uses: frequenz-floss/gh-action-setup-python-with-deps@v1.0.0
        with:
          python-version: ${{ matrix.python }}
          dependencies: dist/*.whl

      - name: Print installed packages (debug)
        run: python -m pip freeze

  # This job runs if all the `test-installation` matrix jobs ran and succeeded.
  # It is only used to have a single job that we can require in branch
  # protection rules, so we don't have to update the protection rules each time
  # we add or remove a job from the matrix.
  test-installation-all:
    # The job name should match the name of the `test-installation` job.
    name: Test package installation
    needs: ["test-installation"]
    # We skip this job only if test-installation was also skipped
    if: always() && needs.test-installation.result != 'skipped'
    runs-on: ubuntu-24.04
    env:
      DEPS_RESULT: ${{ needs.test-installation.result }}
    steps:
      - name: Check matrix job result
        run: test "$DEPS_RESULT" = "success"

  test-docs:
    name: Test documentation website generation
    if: github.event_name != 'push'
    runs-on: ubuntu-24.04
    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Fetch sources
        uses: actions/checkout@v4
        with:
          submodules: true

      - name: Setup Python
        uses: frequenz-floss/gh-action-setup-python-with-deps@v1.0.0
        with:
          python-version: ${{ env.DEFAULT_PYTHON_VERSION }}
          dependencies: .[dev-mkdocs]

      - name: Generate the documentation
        env:
          MIKE_VERSION: gh-${{ github.job }}
        run: |
          mike deploy $MIKE_VERSION
          mike set-default $MIKE_VERSION

      - name: Upload site
        uses: actions/upload-artifact@v4
        with:
          name: docs-site
          path: site/
          if-no-files-found: error

  publish-docs:
    name: Publish documentation website to GitHub pages
    needs: ["nox-all", "test-installation-all"]
    if: github.event_name == 'push'
    runs-on: ubuntu-24.04
    permissions:
      contents: write
    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Fetch sources
        uses: actions/checkout@v4
        with:
          submodules: true

      - name: Setup Python
        uses: frequenz-floss/gh-action-setup-python-with-deps@v1.0.0
        with:
          python-version: ${{ env.DEFAULT_PYTHON_VERSION }}
          dependencies: .[dev-mkdocs]

      - name: Calculate and check version
        id: mike-version
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
          GIT_REF: ${{ github.ref }}
          GIT_SHA: ${{ github.sha }}
        run: |
          python -m frequenz.repo.config.cli.version.mike.info

      - name: Fetch the gh-pages branch
        if: steps.mike-version.outputs.version
        run: git fetch origin gh-pages --depth=1

      - name: Build site
        if: steps.mike-version.outputs.version
        env:
          VERSION: ${{ steps.mike-version.outputs.version }}
          TITLE: ${{ steps.mike-version.outputs.title }}
          ALIASES: ${{ steps.mike-version.outputs.aliases }}
          # This is not ideal, we need to define all these variables here
          # because we need to calculate all the repository version information
          # to be able to show the correct versions in the documentation when
          # building it.
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
          GIT_REF: ${{ github.ref }}
          GIT_SHA: ${{ github.sha }}
        run: |
          mike deploy --update-aliases --title "$TITLE" "$VERSION" $ALIASES

      - name: Sort site versions
        if: steps.mike-version.outputs.version
        run: |
          git checkout gh-pages
          python -m frequenz.repo.config.cli.version.mike.sort versions.json
          git commit -a -m "Sort versions.json"

      - name: Publish site
        if: steps.mike-version.outputs.version
        run: |
          git push origin gh-pages

  create-github-release:
    name: Create GitHub release
    needs: ["publish-docs"]
    # Create a release only on tags creation
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    permissions:
      # We need write permissions on contents to create GitHub releases and on
      # discussions to create the release announcement in the discussion forums
      contents: write
      discussions: write
    runs-on: ubuntu-24.04
    steps:
      - name: Download distribution files
        uses: actions/download-artifact@v4
        with:
          name: dist-packages
          path: dist

      - name: Download RELEASE_NOTES.md
        run: |
          set -ux
          gh api \
              -X GET \
              -f ref=$REF \
              -H "Accept: application/vnd.github.raw" \
              "/repos/$REPOSITORY/contents/RELEASE_NOTES.md" \
            > RELEASE_NOTES.md
        env:
          REF: ${{ github.ref }}
          REPOSITORY: ${{ github.repository }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Create GitHub release
        run: |
          set -ux
          extra_opts=
          if echo "$REF_NAME" | grep -- -; then extra_opts=" --prerelease"; fi
          gh release create \
            -R "$REPOSITORY" \
            --notes-file RELEASE_NOTES.md \
            --generate-notes \
            $extra_opts \
            $REF_NAME \
            dist/*
        env:
          REF_NAME: ${{ github.ref_name }}
          REPOSITORY: ${{ github.repository }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  publish-to-pypi:
    name: Publish packages to PyPI
    needs: ["create-github-release"]
    runs-on: ubuntu-24.04
    permissions:
      # For trusted publishing. See:
      # https://blog.pypi.org/posts/2023-04-20-introducing-trusted-publishers/
      id-token: write
    steps:
      - name: Download distribution files
        uses: actions/download-artifact@v4
        with:
          name: dist-packages
          path: dist

      - name: Publish the Python distribution to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
"""

NEW_CI_API = r"""name: CI

on:
  merge_group:
  push:
    # We need to explicitly include tags because otherwise when adding
    # `branches-ignore` it will only trigger on branches.
    tags:
      - '*'
    branches-ignore:
      # Ignore pushes to merge queues.
      # We only want to test the merge commit (`merge_group` event), the hashes
      # in the push were already tested by the PR checks
      - 'gh-readonly-queue/**'
      - 'dependabot/**'
  workflow_dispatch:

env:
  # Please make sure this version is included in the `matrix`, as the
  # `matrix` section can't use `env`, so it must be entered manually
  DEFAULT_PYTHON_VERSION: '3.11'
  # It would be nice to be able to also define a DEFAULT_UBUNTU_VERSION
  # but sadly `env` can't be used either in `runs-on`.

jobs:
  protolint:
    name: Check proto files with protolint
    runs-on: ubuntu-24.04

    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Fetch sources
        uses: actions/checkout@v3
        with:
          submodules: true

      - name: Run protolint
        # Only use hashes here, as we are passing the github token, we want to
        # make sure updates are done consciously to avoid security issues if the
        # action repo gets hacked
        uses: yoheimuta/action-protolint@e94cc01b1ad085ed9427098442f66f2519c723eb # v1.0.0
        with:
          fail_on_error: true
          filter_mode: nofilter
          github_token: ${{ secrets.github_token }}
          protolint_flags: proto/
          protolint_version: "0.53.0"
          reporter: github-check

  nox:
    name: Test with nox
    strategy:
      fail-fast: false
      matrix:
        arch:
          - amd64
          - arm
        os:
          - ubuntu-24.04
        python:
          - "3.11"
          - "3.12"
        nox-session:
          # To speed things up a bit we use the special ci_checks_max session
          # that uses the same venv to run multiple linting sessions
          - "ci_checks_max"
          - "pytest_min"
    runs-on: ${{ matrix.os }}${{ matrix.arch != 'amd64' && format('-{0}', matrix.arch) || '' }}

    steps:
      - name: Run nox
        uses: frequenz-floss/gh-action-nox@v1.0.0
        with:
          python-version: ${{ matrix.python }}
          nox-session: ${{ matrix.nox-session }}
          # TODO(cookiecutter): Uncomment this for projects with private dependencies
          # git-username: ${{ secrets.GIT_USER }}
          # git-password: ${{ secrets.GIT_PASS }}

  # This job runs if all the `nox` matrix jobs ran and succeeded.
  # It is only used to have a single job that we can require in branch
  # protection rules, so we don't have to update the protection rules each time
  # we add or remove a job from the matrix.
  nox-all:
    # The job name should match the name of the `nox` job.
    name: Test with nox
    needs: ["nox"]
    # We skip this job only if nox was also skipped
    if: always() && needs.nox.result != 'skipped'
    runs-on: ubuntu-24.04
    env:
      DEPS_RESULT: ${{ needs.nox.result }}
    steps:
      - name: Check matrix job result
        run: test "$DEPS_RESULT" = "success"

  build:
    name: Build distribution packages
    # Since this is a pure Python package, we only need to build it once. If it
    # had any architecture specific code, we would need to build it for each
    # architecture.
    runs-on: ubuntu-24.04

    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Fetch sources
        uses: actions/checkout@v4
        with:
          submodules: true

      - name: Setup Python
        uses: frequenz-floss/gh-action-setup-python-with-deps@v1.0.0
        with:
          python-version: ${{ env.DEFAULT_PYTHON_VERSION }}
          dependencies: build

      - name: Build the source and binary distribution
        run: python -m build

      - name: Upload distribution files
        uses: actions/upload-artifact@v4
        with:
          name: dist-packages
          path: dist/
          if-no-files-found: error

  test-installation:
    name: Test package installation
    needs: ["build"]
    strategy:
      fail-fast: false
      matrix:
        arch:
          - amd64
          - arm
        os:
          - ubuntu-24.04
        python:
          - "3.11"
          - "3.12"
    runs-on: ${{ matrix.os }}${{ matrix.arch != 'amd64' && format('-{0}', matrix.arch) || '' }}

    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Print environment (debug)
        run: env

      - name: Download package
        uses: actions/download-artifact@v4
        with:
          name: dist-packages
          path: dist

      # This is necessary for the `pip` caching in the setup-python action to work
      - name: Fetch the pyproject.toml file for this action hash
        env:
          GH_TOKEN: ${{ github.token }}
          REPO: ${{ github.repository }}
          REF: ${{ github.sha }}
        run: |
          set -ux
          gh api \
              -X GET \
              -H "Accept: application/vnd.github.raw" \
              "/repos/$REPO/contents/pyproject.toml?ref=$REF" \
            > pyproject.toml

      - name: Setup Python
        uses: frequenz-floss/gh-action-setup-python-with-deps@v1.0.0
        with:
          python-version: ${{ matrix.python }}
          dependencies: dist/*.whl

      - name: Print installed packages (debug)
        run: python -m pip freeze

  # This job runs if all the `test-installation` matrix jobs ran and succeeded.
  # It is only used to have a single job that we can require in branch
  # protection rules, so we don't have to update the protection rules each time
  # we add or remove a job from the matrix.
  test-installation-all:
    # The job name should match the name of the `test-installation` job.
    name: Test package installation
    needs: ["test-installation"]
    # We skip this job only if test-installation was also skipped
    if: always() && needs.test-installation.result != 'skipped'
    runs-on: ubuntu-24.04
    env:
      DEPS_RESULT: ${{ needs.test-installation.result }}
    steps:
      - name: Check matrix job result
        run: test "$DEPS_RESULT" = "success"

  test-docs:
    name: Test documentation website generation
    if: github.event_name != 'push'
    runs-on: ubuntu-24.04
    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Fetch sources
        uses: actions/checkout@v4
        with:
          submodules: true

      - name: Setup Python
        uses: frequenz-floss/gh-action-setup-python-with-deps@v1.0.0
        with:
          python-version: ${{ env.DEFAULT_PYTHON_VERSION }}
          dependencies: .[dev-mkdocs]

      - name: Generate the documentation
        env:
          MIKE_VERSION: gh-${{ github.job }}
        run: |
          mike deploy $MIKE_VERSION
          mike set-default $MIKE_VERSION

      - name: Upload site
        uses: actions/upload-artifact@v4
        with:
          name: docs-site
          path: site/
          if-no-files-found: error

  publish-docs:
    name: Publish documentation website to GitHub pages
    needs: ["nox-all", "test-installation-all"]
    if: github.event_name == 'push'
    runs-on: ubuntu-24.04
    permissions:
      contents: write
    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Fetch sources
        uses: actions/checkout@v4
        with:
          submodules: true

      - name: Setup Python
        uses: frequenz-floss/gh-action-setup-python-with-deps@v1.0.0
        with:
          python-version: ${{ env.DEFAULT_PYTHON_VERSION }}
          dependencies: .[dev-mkdocs]

      - name: Calculate and check version
        id: mike-version
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
          GIT_REF: ${{ github.ref }}
          GIT_SHA: ${{ github.sha }}
        run: |
          python -m frequenz.repo.config.cli.version.mike.info

      - name: Fetch the gh-pages branch
        if: steps.mike-version.outputs.version
        run: git fetch origin gh-pages --depth=1

      - name: Build site
        if: steps.mike-version.outputs.version
        env:
          VERSION: ${{ steps.mike-version.outputs.version }}
          TITLE: ${{ steps.mike-version.outputs.title }}
          ALIASES: ${{ steps.mike-version.outputs.aliases }}
          # This is not ideal, we need to define all these variables here
          # because we need to calculate all the repository version information
          # to be able to show the correct versions in the documentation when
          # building it.
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
          GIT_REF: ${{ github.ref }}
          GIT_SHA: ${{ github.sha }}
        run: |
          mike deploy --update-aliases --title "$TITLE" "$VERSION" $ALIASES

      - name: Sort site versions
        if: steps.mike-version.outputs.version
        run: |
          git checkout gh-pages
          python -m frequenz.repo.config.cli.version.mike.sort versions.json
          git commit -a -m "Sort versions.json"

      - name: Publish site
        if: steps.mike-version.outputs.version
        run: |
          git push origin gh-pages

  create-github-release:
    name: Create GitHub release
    needs: ["publish-docs"]
    # Create a release only on tags creation
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    permissions:
      # We need write permissions on contents to create GitHub releases and on
      # discussions to create the release announcement in the discussion forums
      contents: write
      discussions: write
    runs-on: ubuntu-24.04
    steps:
      - name: Download distribution files
        uses: actions/download-artifact@v4
        with:
          name: dist-packages
          path: dist

      - name: Download RELEASE_NOTES.md
        run: |
          set -ux
          gh api \
              -X GET \
              -f ref=$REF \
              -H "Accept: application/vnd.github.raw" \
              "/repos/$REPOSITORY/contents/RELEASE_NOTES.md" \
            > RELEASE_NOTES.md
        env:
          REF: ${{ github.ref }}
          REPOSITORY: ${{ github.repository }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Create GitHub release
        run: |
          set -ux
          extra_opts=
          if echo "$REF_NAME" | grep -- -; then extra_opts=" --prerelease"; fi
          gh release create \
            -R "$REPOSITORY" \
            --notes-file RELEASE_NOTES.md \
            --generate-notes \
            $extra_opts \
            $REF_NAME \
            dist/*
        env:
          REF_NAME: ${{ github.ref_name }}
          REPOSITORY: ${{ github.repository }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  publish-to-pypi:
    name: Publish packages to PyPI
    needs: ["create-github-release"]
    runs-on: ubuntu-24.04
    permissions:
      # For trusted publishing. See:
      # https://blog.pypi.org/posts/2023-04-20-introducing-trusted-publishers/
      id-token: write
    steps:
      - name: Download distribution files
        uses: actions/download-artifact@v4
        with:
          name: dist-packages
          path: dist

      - name: Publish the Python distribution to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
"""

NEW_CI_PR = r"""name: Test PR

on:
  pull_request:

env:
  # Please make sure this version is included in the `matrix`, as the
  # `matrix` section can't use `env`, so it must be entered manually
  DEFAULT_PYTHON_VERSION: '3.11'
  # It would be nice to be able to also define a DEFAULT_UBUNTU_VERSION
  # but sadly `env` can't be used either in `runs-on`.

jobs:
  nox:
    name: Test with nox
    runs-on: ubuntu-24.04

    steps:
      - name: Run nox
        uses: frequenz-floss/gh-action-nox@v1.0.0
        with:
          python-version: "3.11"
          nox-session: ci_checks_max
          # TODO(cookiecutter): Uncomment this for projects with private dependencies
          # git-username: ${{ secrets.GIT_USER }}
          # git-password: ${{ secrets.GIT_PASS }}

  test-docs:
    name: Test documentation website generation
    runs-on: ubuntu-24.04
    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Fetch sources
        uses: actions/checkout@v4
        with:
          submodules: true

      - name: Setup Python
        uses: frequenz-floss/gh-action-setup-python-with-deps@v1.0.0
        with:
          python-version: ${{ env.DEFAULT_PYTHON_VERSION }}
          dependencies: .[dev-mkdocs]

      - name: Generate the documentation
        env:
          MIKE_VERSION: gh-${{ github.job }}
        run: |
          mike deploy $MIKE_VERSION
          mike set-default $MIKE_VERSION

      - name: Upload site
        uses: actions/upload-artifact@v4
        with:
          name: docs-site
          path: site/
          if-no-files-found: error
"""

NEW_CI_PR_API = r"""name: Test PR

on:
  pull_request:

env:
  # Please make sure this version is included in the `matrix`, as the
  # `matrix` section can't use `env`, so it must be entered manually
  DEFAULT_PYTHON_VERSION: '3.11'
  # It would be nice to be able to also define a DEFAULT_UBUNTU_VERSION
  # but sadly `env` can't be used either in `runs-on`.

jobs:
  protolint:
    name: Check proto files with protolint
    runs-on: ubuntu-24.04

    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Fetch sources
        uses: actions/checkout@v3
        with:
          submodules: true

      - name: Run protolint
        # Only use hashes here, as we are passing the github token, we want to
        # make sure updates are done consciously to avoid security issues if the
        # action repo gets hacked
        uses: yoheimuta/action-protolint@e94cc01b1ad085ed9427098442f66f2519c723eb # v1.0.0
        with:
          fail_on_error: true
          filter_mode: nofilter
          github_token: ${{ secrets.github_token }}
          protolint_flags: proto/
          protolint_version: "0.53.0"
          reporter: github-check

  nox:
    name: Test with nox
    runs-on: ubuntu-24.04

    steps:
      - name: Run nox
        uses: frequenz-floss/gh-action-nox@v1.0.0
        with:
          python-version: "3.11"
          nox-session: ci_checks_max
          # TODO(cookiecutter): Uncomment this for projects with private dependencies
          # git-username: ${{ secrets.GIT_USER }}
          # git-password: ${{ secrets.GIT_PASS }}

  test-docs:
    name: Test documentation website generation
    runs-on: ubuntu-24.04
    steps:
      - name: Setup Git
        uses: frequenz-floss/gh-action-setup-git@v1.0.0
        # TODO(cookiecutter): Uncomment this for projects with private dependencies
        # with:
        #   username: ${{ secrets.GIT_USER }}
        #   password: ${{ secrets.GIT_PASS }}

      - name: Fetch sources
        uses: actions/checkout@v4
        with:
          submodules: true

      - name: Setup Python
        uses: frequenz-floss/gh-action-setup-python-with-deps@v1.0.0
        with:
          python-version: ${{ env.DEFAULT_PYTHON_VERSION }}
          dependencies: .[dev-mkdocs]

      - name: Generate the documentation
        env:
          MIKE_VERSION: gh-${{ github.job }}
        run: |
          mike deploy $MIKE_VERSION
          mike set-default $MIKE_VERSION

      - name: Upload site
        uses: actions/upload-artifact@v4
        with:
          name: docs-site
          path: site/
          if-no-files-found: error
"""


def apply_patch(patch_content: str) -> None:
    """Apply a patch using the patch utility."""
    subprocess.run(["patch", "-p1"], input=patch_content.encode(), check=True)


def replace_file_contents_atomically(  # noqa; DOC501
    filepath: str | Path,
    old: str,
    new: str,
    count: SupportsIndex = -1,
    *,
    content: str | None = None,
) -> None:
    """Replace a file atomically with new content.

    Args:
        filepath: The path to the file to replace.
        old: The string to replace.
        new: The string to replace it with.
        count: The maximum number of occurrences to replace. If negative, all occurrences are
            replaced.
        content: The content to replace. If not provided, the file is read from disk.

    The replacement is done atomically by writing to a temporary file and
    then moving it to the target location.
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    if content is None:
        content = filepath.read_text(encoding="utf-8")

    content = content.replace(old, new, count)

    # Create temporary file in the same directory to ensure atomic move
    tmp_dir = filepath.parent

    # pylint: disable-next=consider-using-with
    tmp = tempfile.NamedTemporaryFile(mode="w", dir=tmp_dir, delete=False)

    try:
        # Copy original file permissions
        st = os.stat(filepath)

        # Write the new content
        tmp.write(content)

        # Ensure all data is written to disk
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()

        # Copy original file permissions to the new file
        os.chmod(tmp.name, st.st_mode)

        # Perform atomic replace
        os.rename(tmp.name, filepath)

    except BaseException:
        # Clean up the temporary file in case of errors
        tmp.close()
        os.unlink(tmp.name)
        raise


def calculate_file_sha256_skip_lines(filepath: Path, skip_lines: int) -> str | None:
    """Calculate SHA256 of file contents excluding the first N lines.

    Args:
        filepath: Path to the file to hash
        skip_lines: Number of lines to skip at the beginning

    Returns:
        The SHA256 hex digest, or None if the file doesn't exist
    """
    if not filepath.exists():
        return None

    # Read file and normalize line endings to LF
    content = filepath.read_text(encoding="utf-8").replace("\r\n", "\n")
    # Skip first N lines and ensure there's a trailing newline
    remaining_content = "\n".join(content.splitlines()[skip_lines:]) + "\n"
    return hashlib.sha256(remaining_content.encode()).hexdigest()


def manual_step(message: str) -> None:
    """Print a manual step message in yellow."""
    print(f"\033[0;33m>>> {message}\033[0m")


if __name__ == "__main__":
    main()
