# Configure GitHub

The generated templates make some assumptions about how the GitHub repository
is configured. Here is a summary of changes you should do to the repository
to make sure everything works as expected.

## Issues

### Labels

Review the list of labels and add:

* `part:xxx` labels that make sense to the project

* Add a `cmd:skip-release-notes` with the following description:

    > It is not necessary to update release notes for this PR

    And `930F79` as color.

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

### Branches

After importing code to the repository, add the following *Branch protection
rules* (as always this is a guideline, defaults that should be used unless
there is a reason to diverge):

#### Protect matching branches

!!! Note inline end

    This is only to enable the merge queue, all the real protection rules will
    be added afterwards via [rulesets](#rulesets). This is why all other
    protections are disabled here.

Add a rule for the **main branch** (`v0.x.x`) without wildcards so merge queues
can be enabled:

- [ ] Require a pull request before merging
    - [ ] Require approvals: 1
    - [ ] Dismiss stale pull request approvals when new commits are pushed
    - [ ] Require review from Code Owners
    - [ ] Restrict who can dismiss pull request reviews
    - [ ] Allow specified actors to bypass required pull requests
    - [ ] Require approval of the most recent reviewable push
- [ ] Require status checks to pass before merging
    - [ ] Require branches to be up to date before merging
    - **(add all the tests that should pass)**
- [ ] Require conversation resolution before merging
- [ ] Require signed commits
- [ ] Require linear history
- [x] Require merge queue:
    * Maximum pull requests to build: **5**
    * Minimum pull requests to merge: **2** (this should be the only change
      to defaults) or after **5** minutes
    * Maximum pull requests to merge: **5**
    - [x] Only merge non-failing pull requests
    * Consider check failed after **60**
- [ ] Require deployments to succeed before merging
- [ ] Lock branch
- [ ] Do not allow bypassing the above settings
- [ ] Restrict who can push to matching branches (this might be disabled
  while pushing the initial changes)
- Rules applied to everyone including administrators
    - [ ] Allow force pushes
    - [ ] Allow deletions

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
  tags]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Disable.creation.of.non-release.tags.json)
* [Disable creation of other
  branches]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Disable.creation.of.other.branches.json)
* [Disallow removal and force-pushes of
  gh-pages]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Disallow.removal.and.force-pushes.of.gh-pages.json)
* [Protect released
  tags]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Protect.released.tags.json)
* [Protect version
  branches]({{config.repo_url}}/blob/{{ref_name}}/github-rulesets/Protect.version.branches.json)

### Code security and analysis

* Enable *Dependabot version updates* if relevant

## Code

The basic code configuration should be generate using
[repo-config](https://frequenz-floss.github.io/frequenz-repo-config-python/).
