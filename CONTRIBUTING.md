# Contributing to Frequenz Repository Configuration

## Build

You can use `build` to simply build the source and binary distribution:

```sh
python -m pip install build
python -m build
```

## Local development

You can use editable installs to develop the project locally (it will install
all the dependencies too):

```sh
python -m pip install -e .
```

Or you can install all development dependencies (`mypy`, `pylint`, `pytest`,
etc.) in one go too:
```sh
python -m pip install -e .[dev]
```

If you don't want to install all the dependencies, you can also use `nox` to
run the tests and other checks creating its own virtual environments:

```sh
python -m pip install .[dev-noxfile]
nox
```

You can also use `nox -R` to reuse the current testing environment to speed up
test at the expense of a higher chance to end up with a dirty test environment.

### Running tests / checks individually

For a better development test cycle you can install the runtime and test
dependencies and run `pytest` manually.

```sh
python -m pip install .[dev-pytest]  # included in .[dev] too

# And for example
pytest tests/test_*.py
```

Or you can use `nox`:

```sh
nox -R -s pytest -- test/test_*.py
```

The same applies to `pylint` or `mypy` for example:

```sh
nox -R -s pylint -- test/test_*.py
nox -R -s mypy -- test/test_*.py
```

### Golden Tests

To test the generated files using the Cookiecutter templates, the [golden
testing](https://en.wikipedia.org/wiki/Characterization_test) technique is used
to ensure that changes in the templates don't occur unexpectedly.

If a golden test fails, a `diff` of the contents will be provided in the test
results.

Failures in the golden tests could indicate two things:

1. The generated files don't match the golden files because an unintended
   change was introduced. For example, there may be a bug that needs to be fixed
   so that the generated files match the golden files again.

2. The generated files don't match the golden files because an intended change
   was introduced. In this case, the golden files need to be updated.

In the latter case, manually updating files is complicated and error-prone,
please consult [Update the golden test
fixtures](#2-update-the-golden-test-fixtures) below for the recommended way to
update the golden files.

### Modifying Cookiecutter Templates

When you need to make changes to the cookiecutter templates (located in
`cookiecutter/{{cookiecutter.github_repo_name}}/`), there's a specific workflow
to follow. The templates support different project types (actor, api, app, lib,
model) using Jinja2 conditional sections.

#### 1. Make your template changes

Edit the files in the `cookiecutter/` directory. Keep in mind that some files
have conditional sections for different project types.

#### 2. Update the golden test fixtures

After modifying templates, you need to regenerate the golden files so the tests
pass:

```sh
UPDATE_GOLDEN=1 pytest tests/integration/test_cookiecutter_generation.py::test_golden
```

If you renamed or removed files, it's safest to wipe the golden directory first:

```sh
rm -rf tests_golden/
UPDATE_GOLDEN=1 pytest tests/integration/test_cookiecutter_generation.py::test_golden
```

**Please ensure that all introduced changes are intended before updating the
golden files.**

#### 3. Write a migration script

Existing projects using these templates need a way to migrate to the new
version. Update `cookiecutter/migrate.py` to handle this migration. The script
is reset to a blank template (from `.github/cookiecutter-migrate.template.py`)
after each release.

A few guidelines for migration scripts:

- Make them idempotent (safe to run multiple times)
- Print clear messages about what's being done
- Use the helper functions: `replace_file_contents_atomically()` for simple
  replacements, `apply_patch()` for more complex changes

For changes that can't be automated (like GitHub repository settings that
require admin permissions, or changes that would make the script overly
complex), use the `manual_step()` function to clearly communicate to users
what they need to do manually:

```python
manual_step(
    "Update branch protection rules in GitHub settings:\n"
    "    Settings > Branches > Enable 'Require status checks'"
)
```

#### 4. Validate with this repository

Run the migration script on this repository itself to make sure it works:

```sh
python3 cookiecutter/migrate.py
git diff .github/workflows/  # Check the changes look correct
```

Note that some changes (e.g., API-specific features like protolint) won't be
testable on this repository since it's a `lib` type project.

#### 5. Update the release notes

Add an entry to `RELEASE_NOTES.md` describing what changed in the templates.

#### 6. Commit separately

Create two separate commits to keep the history clean:

1. First commit: the template changes, migration script, golden tests, and
   release notes
2. Second commit: the changes to this repository from running the migration

This separation makes it easier to review and understand what changed.

### Building the documentation

To build the documentation, first install the dependencies (if you didn't
install all `dev` dependencies):

```sh
python -m pip install -e .[dev-mkdocs]
```

Then you can build the documentation (it will be written in the `site/`
directory):

```sh
mkdocs build
```

Or you can just serve the documentation without building it using:

```sh
mkdocs serve
```

Your site will be updated **live** when you change your files (provided that
you used `pip install -e .`, beware of a common pitfall of using `pip install`
without `-e`, in that case the API reference won't change unless you do a new
`pip install`).

To build multi-version documentation, we use
[mike](https://github.com/jimporter/mike). If you want to see how the
multi-version sites looks like locally, you can use:

```sh
mike deploy my-version
mike set-default my-version
mike serve
```

`mike` works in mysterious ways. Some basic information:

* `mike deploy` will do a `mike build` and write the results to your **local**
  `gh-pages` branch. `my-version` is an arbitrary name for the local version
  you want to preview.
* `mike set-default` is needed so when you serve the documentation, it goes to
  your newly produced documentation by default.
* `mike serve` will serve the contents of your **local** `gh-pages` branch. Be
  aware that, unlike `mkdocs serve`, changes to the sources won't be shown
  live, as the `mike deploy` step is needed to refresh them.

Be careful not to use `--push` with `mike deploy`, otherwise it will push your
local `gh-pages` branch to the `origin` remote.

That said, if you want to test the actual website in **your fork**, you can
always use `mike deploy --push --remote your-fork-remote`, and then access the
GitHub pages produced for your fork.

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
   Release](https://github.com/frequenz-floss/frequenz-repo-config-python/releases),
   and upload a new package to
   [PyPI](https://pypi.org/project/frequenz-repo-config/)
   automatically.

6. Once this is done, reset the `RELEASE_NOTES.md` with the template:

   ```sh
   cp .github/RELEASE_NOTES.template.md RELEASE_NOTES.md
   cp .github/cookiecutter-migrate.template.py cookiecutter/migrate.py
   ```

   Commit the new release notes and migration script, and create a PR (this step
   should be automated eventually too).

7. Celebrate!
