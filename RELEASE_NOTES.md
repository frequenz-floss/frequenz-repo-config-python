# Frequenz Repository Configuration Release Notes

## Summary

This release improves dependabot groups, so it is less likely that breaking updates are grouped with non-breaking updates and upgrades the GitHub workflows to use more actions, run PR checks faster and use Ubuntu 24.04 instead of 20.04.

## Upgrading

### Cookiecutter template

* Branch protection rule **Protect version branches** was updated, please re-import it following the [instructions](https://frequenz-floss.github.io/frequenz-repo-config-python/v0.13/user-guide/start-a-new-project/configure-github/#rulesets).

    > [!IMPORTANT]
    > For **api** projects make sure to require the **Check proto files with protolint** status check too, which is not included by the provided ruleset by default.

All other upgrading should be done via the migration script or regenerating the templates.

```bash
curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.12/cookiecutter/migrate.py | python3
```

But you might still need to adapt your code:

* The new workflows will test using Python 3.12 too, if your code is not compatible with it, you might need to fix it, or you can just remove the Python 3.12 from the test matrix if you need a quick fix. For example, the `typing-extension` library is compatible with Python 3.12 from version 4.6.0, so you might need to upgrade it if you are using it.
* Check the new dependabot configuration file if you customized the dependabot configuration for the `pip` ecosystem.
* Add exclusions for any other dependency you have at v0.x.x or that breaks frequently, so dependabot PRs are easy to merge.

## New Features

### Cookiecutter template

- Dependabot config now uses a new grouping that should make upgrades more smooth.

    * We group patch updates as they should always work.
    * We also group minor updates, as it works too for most libraries, typically except libraries that don't have a stable release yet (v0.x.x branch), so we make some exceptions for them.
    * Major updates and dependencies excluded by the above groups are still managed, but they'll create one PR per dependency, as breakage is expected, so it might need manual intervention.
    * Finally, we group some dependencies that are related to each other, and usually needs to be updated together.

- The GitHub workflows is now split into PRs and CI workflows.

    These new workflows also start using a new reusable `gh-action-nox`, native arm runners and Ubuntu 24.04, as [Ubuntu 20.04 will be removed from GitHub runners by April's 1st][ubuntu-20.04]. Python 3.12 is also added to the test matrix.

    The PR action is more lightweight, and only tests with one matrix (the most widely used), so PRs can be tested more quickly.

    The push workflow does a more intense testing with all matrix combinations. This also runs for the merge queue, so before PRs are actually merged the tests will run for the complete matrix.

[ubuntu-20.04]: https://github.blog/changelog/2025-01-15-github-actions-ubuntu-20-runner-image-brownout-dates-and-other-breaking-changes/

- The Python `Protect version branches` branch protection rule now request review to Copilot by default.
