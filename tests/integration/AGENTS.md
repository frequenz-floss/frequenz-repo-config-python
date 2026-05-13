# OVERVIEW
This subtree contains the cookiecutter generation integration tests.
It is the author-facing test harness for template changes, not a general pytest area.

# WHERE TO LOOK
- Main workflow: `test_cookiecutter_generation.py`.
- Golden fixtures consumed by this test: `tests_golden/integration/test_cookiecutter_generation/`.
- Template sources under test: `cookiecutter/`.

# TEST STRUCTURE
- `test_golden`: generates repos and compares stdout, stderr, and full trees against golden fixtures.
- `test_generation`: generates repos, creates a venv, installs the generated project, and runs baseline nox checks.
- Cases cover all repository types plus proprietary-license variants.
- Golden case names follow repository type, with `-proprietary` suffixes for non-MIT cases.

# WORKFLOW
- Edit template or migration sources first.
- Run `pytest tests/integration/test_cookiecutter_generation.py::test_golden` to confirm fixture parity.
- When the change is intentional, refresh fixtures with `UPDATE_GOLDEN=1 pytest tests/integration/test_cookiecutter_generation.py::test_golden`.
- Review fixture diffs before keeping them.
- Run `pytest tests/integration/test_cookiecutter_generation.py::test_generation` when you need generated-repo validation beyond tree matching.

# CONVENTIONS
- These tests use `@pytest.mark.integration` and `@pytest.mark.cookiecutter`.
- Golden runs force deterministic environment values (`LANG`, `LANGUAGE`, `LC_ALL`, `GOLDEN_TEST`).
- Generated-repo validation injects `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_FREQUENZ_REPO_CONFIG=0.0.0` to make local installs reproducible.

# ANTI-PATTERNS
- Do not update fixtures without reviewing stdout/stderr and generated-tree changes.
- Do not treat `test_generation` as a substitute for fixture review; it checks runnable output, not golden intent.
