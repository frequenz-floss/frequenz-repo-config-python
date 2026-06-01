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
  merge_group:  # To allow using this as a required check for merging
  pull_request_target:
    types: [opened, synchronize, reopened, labeled, unlabeled]

permissions:
  # Commit migration changes back to the PR branch.
  contents: write
  # Create and normalize migration state labels.
  issues: write
  # Read/update pull request metadata and comments.
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
          # Push migration commits to the PR branch.
          permission-contents: write
          # Manage labels when auto-merging patch-only updates.
          permission-issues: write
          # Approve pull requests and enable auto-merge.
          permission-pull-requests: write
          # Allow pushes when migration changes workflow files.
          permission-workflows: write
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
  Scope this token explicitly with `permission-*` inputs when creating it
  (`contents`, `issues`, `pull-requests`, and `workflows` write).
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
* **`merge_group` trigger** — lets you use the workflow as a required check in
  repositories that gate merges through the merge queue.

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
**skips** PRs containing `the repo-config group`, `Bump black from ` or `Bump
isort from ` in the title.  This ensures those dependency updates are handled
exclusively by their respective migration workflows, while all other
[Dependabot] PRs continue to be auto-approved and merged by the existing
workflow.

The `github-actions` ecosystem updates to the *caller workflow itself* (i.e.
bumping the action's `@<sha>` reference) produce PRs with `the compatible
group` in the title, which does **not** match any migration workflow's `if`
condition.  These PRs are handled normally by `auto-dependabot.yaml`.

## gRPC migration workflow

API projects generated from the template include a workflow
(`grpc-migration.yaml`) that automatically syncs the runtime `>=` floors
for `grpcio` and `protobuf` in `pyproject.toml` after [Dependabot] bumps
the matching build-time pins.

API templates pin `protobuf`, `grpcio` and `grpcio-tools` in
`[build-system].requires` as exact versions and also declare `protobuf`
and `grpcio` in `[project].dependencies` with a `>= <build-pin>` lower
bound.  The lower bound must always match the exact pin: the protobuf
[cross-version runtime guarantee][protobuf-cross-version] requires the
runtime to be at least the version used at generation time.

[Dependabot] correctly bumps `[build-system].requires` but it does not
bump the matching `>=` floor in `[project].dependencies`.  This workflow
runs after a [Dependabot] grpc/protobuf group PR, rewrites the `>=` floor
to match the new build pins, and pushes the fix-up commit back onto the
PR branch.

The workflow uses the
[`dependabot-grpc-fixer.py`][dependabot-grpc-fixer] script shipped by
this repository.  Shipping it as a separate script makes it easy to keep
all API projects updated without regenerating the workflow file, and the
workflow itself stays short.

The companion `auto-dependabot.yaml` workflow skips the
`grpc-compatible`, `grpcio-major` and `protobuf-major` Dependabot groups
so those PRs are handled exclusively by this migration workflow.

The migration script lives at
`cookiecutter/scripts/dependabot-grpc-fixer.py` in this repository, and
the workflow fetches it from the URL configured in `script-url-template`.
The script should be fetched from an immutable release tag or commit
SHA from a trusted source.

### Creating the caller workflow

If you need to set it up in an API project that wasn't generated from the
template (or recreate it), create
`.github/workflows/grpc-migration.yaml` in your repository:

{% raw %}
```yaml
# Automatic grpc/protobuf build/runtime sync for Dependabot PRs
#
# The template's `pyproject.toml` pins `protobuf`, `grpcio` and `grpcio-tools`
# in `[build-system].requires` as *exact* versions, and also declares
# `protobuf` and `grpcio` in `[project].dependencies` with a `>= <build-pin>`
# lower bound.  The lower bound must always match the exact pin, because the
# protobuf cross-version runtime guarantee requires the runtime to be at
# least the version used at generation time:
#   https://protobuf.dev/support/cross-version-runtime-guarantee/
#
# Dependabot correctly bumps `[build-system].requires`, but it does not bump
# the matching `>=` floor in `[project].dependencies`.  This workflow runs
# after a Dependabot grpc/protobuf group PR, rewrites the `>=` floor to match
# the new build pins, and pushes the fix-up commit back onto the PR branch.
#
# The companion auto-dependabot workflow skips the `grpc-compatible`,
# `grpcio-major` and `protobuf-major` groups so those PRs are handled
# exclusively by this migration workflow.
#
# XXX: !!! SECURITY WARNING !!!
# pull_request_target has write access to the repo, and can read secrets.
# This is required because Dependabot PRs are treated as fork PRs: the
# GITHUB_TOKEN is read-only and secrets are unavailable with a plain
# pull_request trigger.  The action mitigates the risk by:
#   - Never executing code from the PR (the migration script is fetched
#     from the repo-config branch configured below, not taken from the PR).
#   - Gating migration steps on github.actor == 'dependabot[bot]' AND the
#     PR title.
#   - Running checkout with persist-credentials: false and isolating
#     push credentials from the migration script environment.
# For more details read:
# https://securitylab.github.com/research/github-actions-preventing-pwn-requests/

name: gRPC Migration

on:
  merge_group:  # To allow using this as a required check for merging
  pull_request_target:
    types: [opened, synchronize, reopened, labeled, unlabeled]

permissions:
  # Commit the sync-up to the PR branch.
  contents: write
  # Create and normalize migration state labels.
  issues: write
  # Read/update pull request metadata and comments.
  pull-requests: write

jobs:
  grpc-migration:
    name: Fix gRPC/protobuf runtime floors
    # Skip if it was triggered by the merge queue. We only need the workflow to
    # be executed to meet the "Required check" condition for merging, but we
    # don't need to actually run the job, having the job present as Skipped is
    # enough.
    if: |
      github.event_name == 'pull_request_target' &&
      github.actor == 'dependabot[bot]' &&
      (contains(github.event.pull_request.title, 'the grpc-compatible group') ||
       contains(github.event.pull_request.title, 'the grpcio-major group') ||
       contains(github.event.pull_request.title, 'the protobuf-major group'))
    runs-on: ubuntu-24.04
    steps:
      - name: Generate token
        id: create-app-token
        uses: actions/create-github-app-token@1b10c78c7865c340bc4f6099eb2f838309f1e8c3 # v3.1.1
        with:
          app-id: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_ID }}
          private-key: ${{ secrets.FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY }}
          # Push the sync-up commit to the PR branch.
          permission-contents: write
          # Create and normalize migration state labels.
          permission-issues: write
          # Read/update pull request metadata and labels.
          permission-pull-requests: write
      - name: Migrate
        uses: frequenz-floss/gh-action-dependabot-migrate@27763fb5eb56476d91abe00132e8a0614171f92f # v1.2.0
        with:
          {% endraw -%}
          script-url-template: >- # {{ ref_name }}
            https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/{{ git.commit }}/cookiecutter/scripts/dependabot-grpc-fixer.py
          {% raw -%}
          token: ${{ steps.create-app-token.outputs.token }}
          version-iteration: "false"
          sign-commits: "true"
          auto-merged-label: "tool:auto-merged"
          migrated-label: "tool:grpc:migration:executed"
          intervention-pending-label: "tool:grpc:migration:intervention-pending"
          intervention-done-label: "tool:grpc:migration:intervention-done"
```
{% endraw %}

The key grpc-specific settings are:

* **`script-url-template`** — points to the
  `dependabot-grpc-fixer.py` script in this repository.  Unlike the
  repo-config migration workflow, the URL has no `{version}` placeholder:
  use the same branch or immutable ref that provides the fixer version you
  want this workflow to run.
* **`if` condition** — matches PRs whose title contains
  `the grpc-compatible group`, `the grpcio-major group` or
  `the protobuf-major group`, which is how [Dependabot] names PRs for the
  matching groups in `.github/dependabot.yml`.
* **`merge_group` trigger** — lets you use the workflow as a required
  check in repositories that gate merges through the merge queue.

!!! Note

    Keep third-party actions pinned to commit hashes.  [Dependabot]
    updates those references through the `github-actions` ecosystem.

!!! Warning "Security"

    The workflow uses `pull_request_target` because [Dependabot] PRs are
    treated as fork PRs: `GITHUB_TOKEN` is read-only and secrets are
    unavailable with a plain `pull_request` trigger.  The action
    mitigates the risk by never executing code from the PR — the
    migration script is fetched from the URL configured in the base
    branch workflow, not from the PR branch.  For details, see
    [Preventing pwn requests][preventing-pwn-requests].

### Requirements

The workflow requires:

* **A [GitHub App][GitHub App]** configured as described in the [GitHub App
  for Dependabot
  workflows](start-a-new-project/configure-github.md#github-app-for-dependabot-workflows)
  section.  The same app used by `auto-dependabot.yaml` and
  `repo-config-migration.yaml` is fine.
* **Auto-merge enabled** in the repository settings (Settings > General >
  Pull Requests > Allow auto-merge).
* **The three new Dependabot groups** in `.github/dependabot.yml`:

    ```yaml
    groups:
      grpc-compatible:
        update-types:
          - "patch"
          - "minor"
        patterns:
          - "grpcio"
          - "grpcio-tools"
          - "protobuf"
      grpcio-major:
        patterns:
          - "grpcio"
          - "grpcio-tools"
      protobuf-major:
        patterns:
          - "protobuf"
    ```

* **The `auto-dependabot.yaml` workflow** must skip these three groups
  in its job-level `if` condition so the migration workflow handles them
  exclusively.

### Interaction with other workflows

The `auto-dependabot.yaml` workflow has a job-level `if` condition that
skips PRs containing `the grpc-compatible group`, `the grpcio-major
group` or `the protobuf-major group` in the title (alongside `the
repo-config group`, `Bump black from ` and `Bump isort from `).  This
ensures those updates are handled exclusively by their respective
migration workflows.

## Black formatting migration workflow

Projects generated from the template also include a workflow
(`black-migration.yaml`) that automatically reformats code when [Dependabot]
upgrades `black` to a new major version.

`black` uses [calendar versioning][calver]: the first component is the year,
the second the month, and the third a patch number.  Its [stability
policy][black-stability] guarantees that formatting output stays unchanged
within the same calendar year, so only the first release of a new year (which
[Dependabot] treats as a **major** bump) may introduce formatting changes.
Minor and patch updates remain in the regular [Dependabot] groups and are
auto-merged normally.

Because major updates are not part of any dependency group, [Dependabot]
already creates an individual PR for them (titled `Bump black from …`).  No
extra dependency group or group exclusions are needed.

The workflow uses the same
[`gh-action-dependabot-migrate`][gh-action-dependabot-migrate] action as the
repo-config migration, but with an **inline migration script** instead of a
URL template.  Because the script is embedded in the workflow YAML on the base
branch (not taken from the PR), the same `pull_request_target` safety model
applies.  It also keeps `auto-merge-on-changes` disabled so reformatted PRs
stay open for manual review.

### Security

The workflow gates execution on **two** conditions:

* `github.actor == 'dependabot[bot]'` — ensures only [Dependabot] can trigger
  it.
* `contains(github.event.pull_request.title, 'Bump black from ')` — limits it
  to individual major `black` update PRs.

The inline script is executed with `python3 -I` (isolated mode) to prevent
importing from the checked-out working directory.  Inside that isolated
interpreter it uses `sys.executable -Im pip` and `sys.executable -Im black`
instead of shelling out to `pip` or `black` directly, and push credentials are
never exposed to the script.

### Requirements

The workflow shares the same [GitHub App][GitHub App] as the repo-config and
auto-dependabot workflows.  No additional secrets are needed — the black
migration script does not make GitHub API calls.

## isort migration workflow

Projects generated from the template also include a workflow
(`isort-migration.yaml`) that automatically reorders imports when [Dependabot]
upgrades `isort`.

`isort` follows [SemVer], but its [release policy][isort-release-policy] is
looser than `black`'s: major releases are for substantial formatting changes,
**minor releases may include intentional formatting changes**, and patch
releases may also adjust output in smaller bug-fix ways.  Because of that,
`isort` is excluded from the regular `patch` and `minor` [Dependabot] groups in
the template's `dependabot.yml`, so every `isort` bump produces an individual
`Bump isort from …` PR and is routed through this migration workflow.

The companion `auto-dependabot.yaml` workflow skips those PRs so they're
handled exclusively by this migration workflow.

The workflow uses the same
[`gh-action-dependabot-migrate`][gh-action-dependabot-migrate] action as the
black migration, with the same **inline migration script** pattern (the script
is embedded in the workflow YAML on the base branch, not taken from the PR).
It also keeps `auto-merge-on-changes` disabled so reordered PRs stay open for
manual review.

### Security

The workflow gates execution on **two** conditions:

* `github.actor == 'dependabot[bot]'` — ensures only [Dependabot] can trigger
  it.
* `contains(github.event.pull_request.title, 'Bump isort from ')` — limits it
  to individual `isort` update PRs.

The inline script is executed with `python3 -I` (isolated mode) to prevent
importing from the checked-out working directory.  Inside that isolated
interpreter it uses `sys.executable -Im pip` and `sys.executable -Im isort`
instead of shelling out to `pip` or `isort` directly, and push credentials are
never exposed to the script.

### Requirements

The workflow shares the same [GitHub App][GitHub App] as the repo-config and
auto-dependabot workflows.  No additional secrets are needed — the isort
migration script does not make GitHub API calls.

It also relies on the template's `dependabot.yml` excluding `isort` from the
`patch` and `minor` groups, so every `isort` update arrives as an individual
PR.

[black-stability]: https://black.readthedocs.io/en/stable/the_black_code_style/index.html#stability-policy
[calver]: https://calver.org/
[isort-release-policy]: https://github.com/PyCQA/isort/blob/main/docs/major_releases/release_policy.md
[SemVer]: https://semver.org/
[Cookiecutter]: https://cookiecutter.readthedocs.io/en/stable
[Dependabot]: https://docs.github.com/en/code-security/dependabot/dependabot-version-updates
[GitHub App]: https://docs.github.com/en/apps/creating-github-apps
[gh-action-dependabot-migrate]: https://github.com/frequenz-floss/gh-action-dependabot-migrate
[dependabot-grpc-fixer]: https://github.com/llucax/frequenz-repo-config-python/blob/fix-grpc-group/cookiecutter/scripts/dependabot-grpc-fixer.py
[migration-workflow]: update-to-a-new-version.md#automated-migration-workflow
[preventing-pwn-requests]: https://securitylab.github.com/research/github-actions-preventing-pwn-requests/
[protobuf-cross-version]: https://protobuf.dev/support/cross-version-runtime-guarantee/
