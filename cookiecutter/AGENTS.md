# OVERVIEW
This subtree is the template-authoring area for `frequenz-repo-config`.
`{{cookiecutter.github_repo_name}}/` is the generated-repo blueprint, not the live repo root.

# STRUCTURE
- `cookiecutter.json`: prompt variables, defaults, extension wiring.
- `hooks/`: pre/post generation validation and fixups.
- `local_extensions.py`: Jinja filters, globals, deterministic golden-test behavior.
- `migrate.py`: upgrade path for existing generated repositories.
- `variable-reference.md`: prompt-field documentation reused in user docs.
- `{{cookiecutter.github_repo_name}}/`: scaffold content shipped to generated projects.

# WHERE TO LOOK
- Add or rename a template variable: `cookiecutter.json`, `local_extensions.py`, `variable-reference.md`.
- Change generated files: `{{cookiecutter.github_repo_name}}/`.
- Change generation-time validation/fixups: `hooks/pre_gen_project.py`, `hooks/post_gen_project.py`.
- Update existing projects after a template change: `migrate.py`.
- Verify scaffold output: `tests/integration/test_cookiecutter_generation.py`, `tests_golden/`.

# WORKFLOW
- Edit template sources in this subtree.
- Refresh golden fixtures with `UPDATE_GOLDEN=1 pytest tests/integration/test_cookiecutter_generation.py::test_golden`.
- Update `cookiecutter/migrate.py` when existing repos need the same change:
  * Be idempotent
  * Use `manual_step()` for non-automatable changes and failures
  * DON'T halt on failure, report and continue applying other changes
  * Adapt existing steps when possible instead of adding new ones that build on top of them
- Validate migration locally with `python3 cookiecutter/migrate.py` and inspect the resulting diff.
- Update `RELEASE_NOTES.md` when the template behavior changes.
- Commit separately (3 commits): templates first, `migrate.py`, and finally this repo's migration result.

# ANTI-PATTERNS
- Do not place maintainer-only guidance inside `{{cookiecutter.github_repo_name}}/` unless it is meant to ship in generated repos.
- Do not change prompt variables without checking `variable-reference.md`, hooks/extensions, and migration impact.
- Do not skip multi-type verification; template edits can affect actor/api/app/lib/model outputs differently.

# NOTES
- `GOLDEN_TEST` handling in `local_extensions.py` and hooks keeps generated output deterministic during fixture refreshes.
- API templates have extra structure (`proto/`, `py/`, `pytests/`) and often need migration care beyond the library/app/actor/model cases.
