# Update an existing project

To update an existing project, you can use the [Cookiecutter *replay
file*](https://cookiecutter.readthedocs.io/en/stable/advanced/replay.html) that
was saved during the project generation. The file is saved as
`.cookiecutter-replay.json`. Using this file, you can re-run [Cookiecutter]
without having to enter all the inputs again.

!!! Warning

    * Don't forget to commit all changes in your repository before doing this!
      Files will be overwritten!
    * Don't forget to check all the [release
      notes](https://github.com/frequenz-floss/frequenz-repo-config-python/releases)
      for all the versions you are going to update, in particular the
      **Upgrading** section, as there might be steps necessary before even
      running the `cookiecutter` command for the update.

```sh
git commit -a  # commit all changes
cd ..
cookiecutter gh:frequenz-floss/frequenz-repo-config-python \
    --directory=cookiecutter \{{ """
    --checkout """ + version.ref_name + " \\" if version}}
    --overwrite-if-exists \
    --replay \
    --replay-file project-directory/.cookiecutter-replay.json
```

This will create a new commit with all the changes to the overwritten files.
Bear in mind that all the `TODO`s will come back, so there will be quite a bit
of cleanup to do. You can easily check what was changed using `git show`, and
you can use `git commit --amend` to amend the previous commit with the template
updates, or create a new commit with the fixes. You can also use `git citool`
or `git gui` to easily add, remove, or even discard (revert) changes in the
templates update commit.

!!! Note

    The `project-directory` is the directory of your previously generated
    project. If you renamed it, then the files will be generated in a new
    directory with the original name. You can update the target directory in
    the replay file.

!!! Note

    Please remember to keep your replay file up to date if you change any
    metadata in the project.

!!! Tip

    Please have a look at the follow-up steps listed in the [Start a new
    project](#create-the-local-development-environment) section to finish the
    setup.
