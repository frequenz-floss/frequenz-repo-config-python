# Configure PyPI

## Configure a trusted publisher

Before a package can be published to [PyPI] after a release, a trusted
publisher needs to be configured.

!!! Note

    You need a [PyPI] account to do this. You can
    [register](https://pypi.org/account/register/) for free.

1. [Log-in](https://pypi.org/account/login/) to [PyPI].

2. Go to the [Publishing](https://pypi.org/manage/account/publishing/) section
   of your account.

3. Scroll down to the section **Add a new pending publisher**, and fill in the fields.

    * **PyPI Project Name:** The name of the package you want to publish.
      Usually is the same as the [GitHub] repository name, removing the `-python`
      suffix if any.

    * **Owner:** The [GitHub] username/organization of the owner of the package.
      For Frequenz projects this is `frequenz-floss`.

    * **Repository name:** The name of the [GitHub] repository of the package.

    * **Workflow name:** `ci.yaml`.

    * **Environment name:** Leave empty.

4. Click on `Add`.

5. Now uploading the new package from [GitHub] should work.

6. After the new package was uploaded / created.

    1. Invite other maintainers to co-maintain the new package.

        1. Go to your account [Projects](https://pypi.org/manage/projects/).
        2. Click on **Manage** for the new package.
        3. Click on **Collaborators**.
        4. Scroll down to the section **Invite collaborator**.
        5. Fill in the **Username** and the appropriate **Role** for the new
           collaborator.
        6. Click on **Add**.
        7. Repeat steps to add more collaborators.

[PyPI]: https://pypi.org/
[GitHub]: https://github.com/
