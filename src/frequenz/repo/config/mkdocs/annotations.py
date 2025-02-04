# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Code annotations using numbers.

This module is provided almost exclusively as a documentation source.

# Introduction

Normally annotations are shown with a `(+)` button that expands the annotation. To be
able to explain code step by step, it is good to have annotations with numbers, shown as
`(1)`, `(2)`, etc., to be able to follow the notes in a particular order.

To do this, we need some custom CSS rules. Before this customization was officially
supported and documented, but now they are not officially supported anymore, so it could
eventually break (it already did once).

If that happens we either need to look into how to fix the CSS ourselves or remove the
feature. To do the customization, this is what we should be able to count on:

> You can be sure that the data-md-annotation-id attribute will always be present in the
> source, which means you can always number them in any way you like.

# How to implement it

To implement numbered annotations, you need to add a custom CSS file to your
`mkdocs.yml` configuration file:

```yaml title="mkdocs.yml"
extra_css:
  - path/to/style.css
```

The CSS file should contain the following rules:

```css title="path/to/style.css"
.md-typeset .md-annotation__index > ::before {
  content: attr(data-md-annotation-id);
}
.md-typeset :focus-within > .md-annotation__index > ::before {
  transform: none;
}
.md-typeset .md-annotation__index {
  width: 4ch;
}
```

# Macros integration

If you want to show an example on how an annotation looks like, you can use the
[`CODE_ANNOTATION_MARKER`][frequenz.repo.config.mkdocs.annotations.CODE_ANNOTATION_MARKER]
variable to inject the appropriate HTML code. See
[frequenz.repo.config.mkdocs.mkdocstrings_macros][] for more information.

# References

* [Code annotation in
   `mkdocs-material`](https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#code-annotations)

* [Original docs on how to enable numbered
   annotations](https://web.archive.org/web/20230724161216/https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#annotations-with-numbers)

* [The PR fixing the numbered annotations when they
   broke](https://github.com/frequenz-floss/frequenz-sdk-python/pull/684)

* [The regression reported when it was decided to drop support for numbered annotations
   officially](https://github.com/squidfunk/mkdocs-material/issues/6042)

* [The `sphinx-immaterial` documentation on how to do numbered
   annotations](https://sphinx-immaterial.readthedocs.io/en/latest/code_annotations.html#annotation-buttons-with-numbers)
"""

CODE_ANNOTATION_MARKER: str = (
    r'<span class="md-annotation">'
    r'<span class="md-annotation__index" tabindex="-1">'
    r'<span data-md-annotation-id="1"></span>'
    r"</span>"
    r"</span>"
)
"""A variable to easily show an example code annotation."""
