# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Frequenz project setup tools and common configuration.

The tools are provided to configure 4 main types of repositories:

- APIs (api)
- Actors (actor)
- Applications (app)
- Libraries (lib)

# Common

## `nox`

Projects wanting to use `nox` to run lint checkers and other utilities can use
the [`frequenz.repo.config.nox`][] package.

Make sure to add this package as `dev` dependency to your project's
`pyproject.tom` file, for example:

```toml
[project.optional-dependencies]
nox = [
    "nox == 2022.11.21",
    "frequenz-repo-config[lib] == 0.1.0",
]
```

Please note the `lib` optional dependency. Make sure you specify the correct
one based on the type of your project (`api`, `actor`, `app`, `lib`). Also make
sure to adjust the versions.

When writing the `noxfile.py` you should import the `nox` module from this
package and use the [`frequenz.repo.config.nox.configure`][] function,
which will configure all nox sessions.

You should call `configure()` using one of the default configurations provided
in the [`frequenz.repo.config.nox.default`][] module. For example:

```python
from frequenz.repo import config

config.nox.configure(config.nox.default.lib_config)
```

Again, make sure to pick the correct default configuration based on the type of
your project (`api_config`, `actor_config`, `app_config`, `lib_config`).

If you need to modify the configuration, you can copy one of the default
configurations by using the
[`copy()`][frequenz.repo.config.nox.config.Config.copy] method:

```python
from frequenz.repo import config

conf = config.nox.default.lib_config.copy()
conf.opts.black.append("--diff")
config.nox.configure(conf)
```

If you need further customization or to define new sessions, you can use the
following modules:

- [`frequenz.repo.config.nox.config`][]: Low-level utilities to configure nox
  sessions. It defines the `Config` and CommandsOptions` classes and the actual
  implementation of the `configure()` function. It also defines the `get()`
  function, which can be used to get the currently used configuration object.

- [`frequenz.repo.config.nox.session`][]: Predefined nox sessions. These are
  the sessions that are used by default.

- [`frequenz.repo.config.nox.util`][]: General purpose utility functions.


# APIs

## `setuptools` gRPC support

When configuring APIs it is assumed that they have a gRPC interface.

Normally Frequenz APIs use basic types from
[`google/api-common-protos`](https://github.com/googleapis/api-common-protos),
so you need to make sure the proper submodule is added to your project:

```sh
mkdir submodules
git submodule add https://github.com:googleapis/api-common-protos.git submodules/api-common-protos
git commit -m "Add Google api-common-protos submodule" submodules/api-common-protos
```

Then you need to create a `setup.py` file with the following content:

```py
import setuptools

from frequenz.repo.config.setuptools import grpc_tools

if __name__ == "__main__":
    setuptools.setup(cmdclass=grpc_tools.build_proto_cmdclass())
```

Then you need to add this package as a build dependency and a few extra
dependencies to your project, for example:

```toml
requires = [
  "setuptools >= 67.3.2, < 68",
  "setuptools_scm[toml] >= 7.1.0, < 8",
  "frequenz-repo-config[api] >= 0.1.0, < 0.2.0",
]
build-backend = "setuptools.build_meta"

[project]
dependencies = [
  "googleapis-common-protos == 1.56.2",
  "grpcio == 1.51.0",
]
```

Note the `api` extra in `frequenz-repo-config[api]`, this will ensure all
dependencies to build the protocol files will be installed when building the
package. Of course you need to replace the version numbers with the correct
ones too.

Finally you need to make sure to include the generated `*.pyi` files in the
source distribution, as well as the Google api-common-protos files, as it
is not handled automatically yet
([#13](https://github.com/frequenz-floss/frequenz-repo-config-python/issues/13)):

```
recursive-include py *.pyi
recursive-include submodules/api-common-protos/google *.proto
```

If you need to customize how the protobuf files are compiled, you can pass
a path to look for the protobuf files, a glob pattern to find the protobuf
files, and a list of paths to include when compiling the protobuf files. By
default `submodules/api-common-protos` is used as an include path, so if
yout configured the submodules in a different path, you need to pass the
correct path to the `include_paths` argument.
"""

from . import nox, setuptools

__all__ = [
    "nox",
    "setuptools",
]
