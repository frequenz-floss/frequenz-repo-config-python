# Configure GitHub

The generated templates make some assumptions about how the GitHub repository
is configured. Here is a summary of changes you should do to the repository
![Settings](../../_img/settings.png){: .align-middle } to make sure everything
works as expected.

## Issues

### Labels

Review the list of labels and add:

* `part:xxx` labels that make sense to the project

* Make sure there is a `cmd:skip-release-notes` label, and if there isn't,
  create one with `930F79` as color and the following description:

    > It is not necessary to update release notes for this PR

* All labels used by automation in the project, for example look for labels listed in:

    * `.github/keylabeler.yml`
    * `.github/labeler.yml`
    * `.github/dependabot.yml`
    * `.github/workflows/release-notes-check.yml`

## Discussions

This depends on the repo, but in general we want this:

* Remove the *Show and tell* and *Poll* categories

* Rename the *Q&A* category to *Support* and change the emoji to :sos:

  This one is important to match the link provided in `.github/ISSUE_TEMPLATE/config.yml`.

## Settings

### General

#### Default branch

* Rename to `v0.x.x` (this is required for the common CI to work properly when creating releases)

#### Features

- [ ] Wikis
- [x] Issues
- [ ] Sponsorships
- [x] Projects
- [x] Preserve this repository
- [x] Discussions

#### Pull Requests

- [x] Allow merge commits: Default to pull request title and description
- [ ] Allow squash merging
- [ ] Allow rebase merging
- [ ] Always suggest updating pull request branches
- [x] Allow auto-merge
- [x] Automatically delete head branches

#### Archives

- [ ] Include Git LFS objects in archives

#### Pushes

- [x] Limit how many branches and tags can be updated in a single push: 5

### Collaborators and teams

* Give the team owning the repository *Role: Admin*
* Give *everybody* team *Role: Triage*

### Rules

#### Rulesets

![Importing rulesets](../../_img/import-rulesets.png)

Import the following
[rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets):

!!! Note inline end

    You might need to adapt the status checks in the *Protect version
    branches* ruleset depending on your repository configuration.

{% set ref_name = version.ref_name if version else default_branch %}

* [Disable creation of non-release
  tags]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Disable creation of non-release tags.json)
* [Disable creation of other
  branches]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Disable creation of other branches.json)
* [Disallow removal and force-pushes of
  gh-pages]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Disallow removal and force-pushes of gh-pages.json)
* [Protect released
  tags]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Protect released tags.json)
* [Queue PRs for the default
  branch]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Queue PRs for the default branch.json)

##### Python specific rulesets

* [Protect version
  branches]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/python/Protect version branches.json)

##### Rust specific rulesets

* [Protect version
  branches]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/rust/Protect version branches.json)

### Code security and analysis

* Enable *Dependabot version updates* if relevant

#### Auto-merge Dependabot PRs (GitHub App)

The templates include an `.github/workflows/auto-dependabot.yaml` workflow that
auto-approves and enables auto-merge for Dependabot PRs.

This workflow uses a GitHub App installation token (not `GITHUB_TOKEN`). This is
intentional: actions performed with `GITHUB_TOKEN` do not trigger certain
follow-up workflow runs, which can prevent merge queue CI (`merge_group`) from
starting.

To make it work, ensure:

* The GitHub App is installed on the repository.
* The following secrets are available to the workflow (typically as org secrets):
  `FREQUENZ_AUTO_DEPENDABOT_APP_ID` and `FREQUENZ_AUTO_DEPENDABOT_APP_PRIVATE_KEY`.
* The app installation has sufficient repository permissions to approve/label
  and enable auto-merge. In practice, this means at least `Pull requests: write`
  and `Contents: write`.

## Code

The basic code configuration should be generate using
[repo-config](https://frequenz-floss.github.io/frequenz-repo-config-python/).

## GitHub Pages

No special configuration is needed for GitHub Pages, but you need to initialize
the `gh-pages` branch. You can read how to do this in the [Initialize GitHub
Pages](index.md#initialize-github-pages.md) section.
