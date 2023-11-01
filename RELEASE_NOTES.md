# Frequenz Repository Configuration Release Notes

## Upgrading

### Cookiecutter template

Instead of regenerating the templates, you can simply:

- Run this command to fix the typo and wrong `cli` package:

  ```sh
  sed -i 's/annothations/annotations/' docs/_css/style.css
  sed -i 's/frequenz\.repo\.config\.cli\.version\.mkdocs\.sort/frequenz.repo.config.cli.version.mike.sort/' .github/workflows/ci.yaml
  ```

- Replace the comment after the copyright notice in `.github/containers/nox-cross-arch/arm64-ubuntu-20.04-python-3.11.Dockerfile` with:

  ```Dockerfile
  # This Dockerfile is used to run the tests in arm64, which is not supported by
  # GitHub Actions at the moment.
  ```

## Bug Fixes

### Cookiecutter template

- docs: Fix typo in `docs/_css/style.css` ("annothations" -> "annotations")
- ci: Fix the description of the arm64 `Dockerfile`
