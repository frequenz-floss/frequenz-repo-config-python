# Frequenz Repository Configuration Release Notes

## Summary

This release is a major step and adds many features and breaking changes.

## Upgrading

Since this projects is still in very heavy devepoment, the easiest way to
upgrade is to just regenerate the templates.  Please follow the instructions in
the new documentation website about [updating
projects](https://frequenz-floss.github.io/frequenz-repo-config-python/next/#update-an-existing-project).

## New Features

This is just a quick (non-comprehensive) summary of the new features:

* Add `--diff` as a default argument for `isort`
* Improve `README`
* Don't import modules into packages
* Support migrating and updating existing projects with Cookiecutter
* Cookiecutter template

  * Add `dependabot` configuration
  * Add issue templates, keyword labeler and PR labeler
  * Add `CODEOWNERS` file
  * Add `direnv`-related files to `.gitignore`
  * Add GitHub CI workflow to `cookiecutter`
  * Add `CONTRIBUTING` guide to `cookiecutter`
  * Add `RELEASE_NOTES` to `cookiecutter`
  * Add support to generate documentation using `mkdocs`

* Apply all the Cookiecutter template improvements to this project

## Bug Fixes

This is just a quick (non-comprehensive) summary of bug fixes:

* Fix some comments about creating labels
* Fix tests
