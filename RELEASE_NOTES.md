# Frequenz Repository Configuration Release Notes

## Summary

This release upgrades `mike` to 2.0.0.

## Upgrading

### Cookiecutter template

There is no need to re-generate the cookiecutter template for this release. Instead you can upgrade the `mike` package in your `pyproject.toml` file and add the new `alias_type: redirect` option to the `plugins.mike` key in the `mkdocs.yml` file.

You should be able to do this by running the following commands:

```sh
sed -i '/canonical_version: latest/ i\      alias_type: redirect' mkdocs.yml
sed -i 's/  "mike == .*",/  "mike == 2.0.0",/' pyproject.toml
```

Please make sure to check the diff and test if everything works as expected. After doing a `git diff` you should get something like:

```diff
diff --git a/mkdocs.yml b/mkdocs.yml
index 3d0f82e..6adfbe8 100644
--- a/mkdocs.yml
+++ b/mkdocs.yml
@@ -93,6 +93,7 @@ plugins:
   - literate-nav:
       nav_file: SUMMARY.md
   - mike:
+      alias_type: redirect
       canonical_version: latest
   - mkdocstrings:
       custom_templates: templates
diff --git a/pyproject.toml b/pyproject.toml
index 9a1604b..b183524 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -47,7 +47,7 @@ dev-formatting = ["black == 23.10.1", "isort == 5.12.0"]
 dev-mkdocs = [
   "black == 23.10.1",
   "Markdown==3.5.1",
-  "mike == 1.1.2",
+  "mike == 2.0.0",
   "mkdocs-gen-files == 0.5.0",
   "mkdocs-literate-nav == 0.6.1",
   "mkdocs-material == 9.4.7",
```

If that's not the case, your `pyproject.toml` and/or `mkdocs.yml` files might have been diverged from the generated files and updated in a way that is not compatible with the upgrade. In that case you'll have to fix it manually or re-generate the templates.
