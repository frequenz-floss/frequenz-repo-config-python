# Frequenz Repository Configuration Release Notes

## Bug Fixes

- Fixed some typos in the docs.
- Fixed wrong comparison for `mike` versions when versions were equal.
- Fixed version regex escaping of `.`. This means that a version like v0x1e1 were accepted as valid semver versions. Now this version is not considered a semver version anymore.
- `setuptools.grpc_tools`: Fix wrong passing of include paths when passed via:

    * Command-line: Now extra white-spaces and empty strings are removed, before they were passed to `protoc -I`.
    * `pyproject.toml`: Now an empty array/list can be passed to override the default paths, before this resulted in an empty string being passed to `protoc -I`.
