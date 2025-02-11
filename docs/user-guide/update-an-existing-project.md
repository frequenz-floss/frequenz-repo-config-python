{% set ref_name = version.ref if version else 'HEAD' %}
# Update an existing project

To upgrade an existing project, there are two main approaches: use a migration
script or re-run the [Cookiecutter] command.

## Use a migration script

This is the recommended approach, as it should be much less work. Only when
extremely deep changes are made to the template, or when the project is very
old, should you consider re-running the [Cookiecutter] command. Usually release
notes will warn you about the former.

The script can't always perform all the changes necessary to migrate to a new
version. In this case, you will have to manually apply the changes. The script
will guide you through the process, so please read the script output carefully.

The script can also only migrate from one version to the next. If you are
skipping versions, you will have to run the script multiple times.

The easiest way to run the migration script is to fetch it from GitHub and run
it directly.

```sh
curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/{{ ref_name }}/cookiecutter/migrate.py \
	| python3
```

Make sure that the version (`{{ ref_name }}`) matches the
target version you are migrating to.

!!! Tip "Tip for MacOS users"

    The migration script may not work out of the box on macOS. You need to
    install `coreutils` to ensure compatibility:

    ```sh
    brew install coreutils gnu-sed
    ```

    After installation, update your `PATH` in your shell configuration
    (e.g. ~/.zshrc) so that the system uses the GNU versions. Depending on
    where the packages are installed this might look like this:

    ```sh
    export PATH="/opt/homebrew/opt/coreutils/libexec/gnubin:/opt/homebrew/opt/gnu-sed/libexec/gnubin:$PATH"
    export MANPATH="/opt/homebrew/opt/coreutils/libexec/gnuman:$MANPATH"
    ```

    Then, source your configuration file again to apply the changes:

    ```sh
    source ~/.zshrc  # or ~/.bashrc, depending on your shell
    ```

## Re-run the Cookiecutter command

If you are upgrading a very old project (jumping multiple versions at the time)
it is probably easier to just regenerate the whole project.

To do so, you can use the [Cookiecutter *replay
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
