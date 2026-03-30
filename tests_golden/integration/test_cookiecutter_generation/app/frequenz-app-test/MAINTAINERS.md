# Maintainers' Guide

This document describes the process for maintaining the project.

## Releasing

These are the steps to create a new release:

1. Get the latest head you want to create a release from.

2. Update the `RELEASE_NOTES.md` file if it is not complete, up to date, and
   remove template comments (`<!-- ... ->`) and empty sections. Submit a pull
   request if an update is needed, wait until it is merged, and update the
   latest head you want to create a release from to get the new merged pull
   request.

3. Create a new signed tag using the release notes and
   a [semver](https://semver.org/) compatible version number with a `v` prefix,
   for example:

   ```sh
   git tag -s --cleanup=whitespace -F RELEASE_NOTES.md v0.0.1
   ```

4. Push the new tag.

5. A GitHub action will test the tag and if all goes well it will create
   a [GitHub
   Release](https://github.com/frequenz-floss/frequenz-app-test/releases),
   and upload a new package to
   [PyPI](https://pypi.org/project/frequenz-app-test/)
   automatically.

6. Once this is done, reset the `RELEASE_NOTES.md` with the template:

   ```sh
   cp .github/RELEASE_NOTES.template.md RELEASE_NOTES.md
   ```

   Commit the new release notes and create a PR (this step should be automated
   eventually too).

7. Celebrate!

## Upgrading dependencies

### [repo-config]

Frequenz projects have a common structure, so we use [cookiecutter] templates
to generate them. [repo-config] provides this template, and also many small tools to
ensure consistency across repositories and to glue and fill some gaps when
combining the tools we use.

Some work is needed when upgrading [repo-config] to a new version. Usually
following the release notes and the [upgrade
guide](https://frequenz-floss.github.io/frequenz-repo-config-python/latest/user-guide/update-an-existing-project/)
is enough.

[repo-config]: https://frequenz-floss.github.io/frequenz-repo-config-python/
[cookiecutter]: https://cookiecutter.readthedocs.io/

##  Cross-Arch Testing

This project has built-in support for testing across multiple architectures.
Currently, our CI conducts tests on `arm64` machines using QEMU emulation. We
also have the flexibility to expand this support to include additional
architectures in the future.

This project contains Dockerfiles that can be used in the CI to test the
python package in non-native machine architectures, e.g., `arm64`. The
Dockerfiles exist in the directory `.github/containers/nox-cross-arch`, and
follow a naming scheme so that they can be easily used in build matrices in the
CI, in `nox-cross-arch` job. The naming scheme is:

```
<arch>-<os>-python-<python-version>.Dockerfile
```

E.g.,

```
arm64-ubuntu-20.04-python-3.11.Dockerfile
```

If a Dockerfile for your desired target architecture, OS, and python version
does not exist here, please add one before proceeding to add your options to
the test matrix.
