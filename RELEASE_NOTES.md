# Frequenz Repository Configuration Release Notes

## Summary

This release fixes the building of distribution packages.

## Bug Fixes

- Fixed the building of distribution packages, which was failing with `setuptools-scm was unable to detect version`. When building a wheel from a source distribution there is no git repository to get the version from, so `setuptools-scm` 10.0.x reads it from `PKG-INFO` using an entry point provided by `vcs-versioning`, but it doesn't declare any upper bound for it. `vcs-versioning` 2.x dropped that entry point and moved the fallback to `setuptools-scm` itself, so builds started failing as soon as `vcs-versioning` 2.x was picked up. `setuptools-scm` was updated to 10.2.1, which provides the fallback again and bounds `vcs-versioning` to the 2.x series.
