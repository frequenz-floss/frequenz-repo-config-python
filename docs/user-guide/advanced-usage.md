{% set ref_name = version.ref_name if version else default_branch %}

# Advanced usage

The [Cookiecutter] template uses some tools provided as a library by this
project.

Usually, users don't need to deal with it directly, but if your project needs
some extra customization (like disabling `nox` sessions or adding new ones, or
using different CLI options for some tools), then you'll need to.

You can find information about the extra features in the [API
reference](reference/frequenz/repo/config/).

## Migration workflow

Projects generated from the template already include the automated migration
workflow (`repo-config-migration.yaml`).  If you need to set it up in a
project that wasn't generated from the template (or need to recreate it),
follow the steps below.

The migration workflow uses the
[`gh-action-dependabot-migrate`][gh-action-dependabot-migrate] GitHub Action,
which contains all the migration logic (running scripts, committing changes,
posting comments, managing labels, approving and merging).  The workflow in
your repository triggers the action with repo-config-specific inputs.

See the [`gh-action-dependabot-migrate`
documentation][gh-action-dependabot-migrate] for full details on the action's
inputs, authentication options, trust model, and security design.

For general information about how the workflow works and how to interact with
it as a user, see the [automated migration workflow][migration-workflow]
section in the update guide.

### Creating the caller workflow

Create `.github/workflows/repo-config-migration.yaml` in your repository:

{% raw %}
```yaml
name: Repo Config Migration

on:
  pull_request_target:
    types: [opened, synchronize, reopened, labeled, unlabeled]

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  repo-config-migration:
    name: Migrate Repo Config
    if: contains(github.event.pull_request.title, 'the repo-config group')
    runs-on: ubuntu-24.04
    steps:
      - name: Generate token
        id: create-app-token
        uses: actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf # v2.2.1
        with:
          app-id: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_ID }}
          private-key: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY }}
      - name: Migrate
        uses: frequenz-floss/gh-action-dependabot-migrate@07dc7e74726498c50726a80cc2167a04d896508f # v1.0.0
        with:
          script-url-template: >-
            https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/{version}/cookiecutter/migrate.py
          token: ${{ steps.create-app-token.outputs.token }}
          migration-token: ${{ secrets.REPO_CONFIG_MIGRATION_TOKEN }}
          sign-commits: "true"
          auto-merged-label: "tool:auto-merged"
          migrated-label: "tool:repo-config:migration:executed"
          intervention-pending-label: "tool:repo-config:migration:intervention-pending"
          intervention-done-label: "tool:repo-config:migration:intervention-done"
```
{% endraw %}

!!! Note

    Keep third-party actions pinned to commit hashes.
    [Dependabot] updates those references through the `github-actions`
    ecosystem.

The key repo-config-specific settings are:

* **`script-url-template`** — points to the `migrate.py` script in this
  repository, with `{version}` as a placeholder for the version tag (e.g.
  `v0.15.0`).
* **`token`** — a [GitHub App][GitHub App] installation token used for
  pushing migration commits and managing PR state (approval and auto-merge,
  when applicable).
  Because it is not `GITHUB_TOKEN`, API calls made with this token trigger
  follow-up workflows (merge queue CI, status checks, etc.).
* **`migration-token`** — a token exposed to the migration script as
  `GH_TOKEN` / `GITHUB_TOKEN` for authenticated GitHub API calls (e.g.
  updating repository settings or branch rulesets).
* **`auto-merge-on-changes`** — intentionally omitted, so it uses the
  action's default (`false`). If the migration produces file changes
  (commits), the PR is left for manual review, approval, and merge.
* **`auto-merged-label`** — set to `tool:auto-merged` (shared with the
  `auto-dependabot.yaml` workflow) so auto-merged PRs are consistently
  labelled.
* **`migrated-label`**, **`intervention-pending-label`**,
  **`intervention-done-label`** — custom label names following the
  `tool:repo-config:migration:*` naming convention.
* **`if` condition** — matches PRs with `the repo-config group` in the
  title, which is how [Dependabot] names PRs for the `repo-config`
  dependency group.

!!! Warning "Security"

    The workflow uses `pull_request_target` because [Dependabot] PRs are
    treated as fork PRs: `GITHUB_TOKEN` is read-only and secrets are
    unavailable with a plain `pull_request` trigger.  The action mitigates
    the risk by never executing code from the PR — the migration script is
    fetched from an upstream tag.  For details, see [Preventing pwn
    requests](https://securitylab.github.com/research/github-actions-preventing-pwn-requests/).

### Requirements

The workflow requires:

* **A [GitHub App][GitHub App]** configured as described in the [GitHub App
  for Dependabot
  workflows](start-a-new-project/configure-github.md#github-app-for-dependabot-workflows)
  section.

* **A `REPO_CONFIG_MIGRATION_TOKEN` secret** — a token (e.g. a fine-grained PAT) that
  gives the migration script access to the GitHub API.  See the [GitHub App
  for Dependabot
  workflows](start-a-new-project/configure-github.md#github-app-for-dependabot-workflows)
  section for details.

  **Only necessary if the migration script needs to make authenticated API
  calls, it can be left empty otherwise.**

* **Auto-merge enabled** in the repository settings (Settings > General >
  Pull Requests > Allow auto-merge).

* **A `repo-config` dependency group** in `.github/dependabot.yml` that
  groups `frequenz-repo-config*` packages:

    ```yaml
    groups:
      repo-config:
        patterns:
          - "frequenz-repo-config*"
    ```

* **A `github-actions` ecosystem** in `.github/dependabot.yml` so the
  action version stays up to date:

    ```yaml
    - package-ecosystem: "github-actions"
      directory: "/"
      schedule:
        interval: "monthly"
    ```

### Interaction with other workflows

The `auto-dependabot.yaml` workflow has a job-level `if` condition that
**skips** PRs containing `the repo-config group` in the title. This ensures
repo-config dependency updates are handled exclusively by the migration
workflow, while all other [Dependabot] PRs continue to be auto-approved and
merged by the existing workflow.

The `github-actions` ecosystem updates to the *caller workflow itself* (i.e.
bumping the action's `@<sha>` reference) produce PRs with `the compatible
group` in the title, which does **not** match the migration workflow's `if`
condition.  These PRs are handled normally by `auto-dependabot.yaml`.

[Cookiecutter]: https://cookiecutter.readthedocs.io/en/stable
[Dependabot]: https://docs.github.com/en/code-security/dependabot/dependabot-version-updates
[GitHub App]: https://docs.github.com/en/apps/creating-github-apps
[gh-action-dependabot-migrate]: https://github.com/frequenz-floss/gh-action-dependabot-migrate
[migration-workflow]: update-to-a-new-version.md#automated-migration-workflow
