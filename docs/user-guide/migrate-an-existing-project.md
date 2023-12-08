# Migrate an existing project

The easiest way to migrate an existing project is to generate a new one based
on the current project metadata and then overwrite the existing files.

It is recommended to commit all changes before doing this, so you can then use
`git` to look at the changes.

If you generate the new repo in a temporary directory, you can easily overwrite
the files in your existing project by using `rsync` or similar tools:

```sh
cd /tmp
cookiecutter gh:frequenz-floss/frequenz-repo-config-python \
    --directory=cookiecutter{{(" --checkout " + version.ref_name) if version}}
rsync -vr --exclude=.git/ new-project/ /path/to/existing/project
cd /path/to/existing/project
git diff
# Fix all the `TODO`s and clean up the generated files
git commit -a
```

!!! Warning

    The trailing slash in `new-project/` and the lack of it in
    `/path/to/existing/project` are meaningful to `rsync`.

    Also, make sure to **exclude** the `.git/` directory to avoid messing up
    with your local Git repository.

!!! Tip

    Please have a look at the follow-up steps listed in the [Start a new
    project](#create-the-local-development-environment) section to finish the
    setup.
