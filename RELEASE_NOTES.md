# Frequenz Repository Configuration Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

- To make the new workflow to check if release notes were updated you should add the check to the branch protection rules of your repository to require this check to pass. You should also add a new label *"cmd:skip-release-notes"* to be able to override the check. You can use the following script to do it:

  ```sh
  repo=...  # org/repo
  token=... # GitHub token with the correct permissions
  name="cmd:skip-release-notes"
  desc="It is not necessary to update release notes for this PR"
  color="930F79"

  # Using cURL
  curl -L \
      -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer $token" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      -d '{"name":"'"$name"'","description":"'"$desc"'","color":"'"$color"'"}' \
      "https://api.github.com/repos/$repo/labels"

  # Using the gh tool (no need for a token if you already have it configured)
  gh api -X POST \
      -f name="$name" -f description="$desc" -f color="$color" \
      "repos/$repo/labels"
  ```

## New Features

- Cookiecutter: Add a new GitHub workflow to check that release notes were updated.

  This workflow will check PRs to see if a change was done in the `src/` directory, and if so, it will fail if the `RELEASE_NOTES.md` wasn't also updated.

  Users can override this by assigning the label `cmd:skip-release-notes` to the PR for changes that don't really need a release notes update.

## Bug Fixes

- Cookiecutter: Now the CI workflow will checkout the submodules.
