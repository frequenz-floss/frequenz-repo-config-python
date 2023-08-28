# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Utilities to build noxfiles.

The main entry point is the [`configure()`][frequenz.repo.config.nox.configure]
function, which will configure all nox sessions according to some configuration.

To use the default options, you should call `configure()` using one of the [repository
types][frequenz.repo.config.RepositoryType].  For example:

```python
from frequenz.repo.config import RepositoryType, nox

nox.configure(RepositoryType.LIB)
```

Again, make sure to pick the correct project typedefault configuration based on the type
of your project (`actor_config`, `api_config`, `app_config`, `lib_config`,
`model_config`).

If you need to use some custom configuration, you can start from the default settings in
the [`frequenz.repo.config.nox.default`][] module,
[copying][frequenz.repo.config.nox.config.Config.copy] it and changing whatever you
need to customize.  For example:

```python
from frequenz.repo.config import nox
from frequenz.repo.config.nox import default

config = default.lib_config.copy()
config.opts.black.append("--diff")
nox.configure(config)
```

If you need further customization or to define new sessions, you can use the
following modules:

- [`frequenz.repo.config.nox.config`][]: Low-level utilities to configure nox sessions.
  It defines the `Config` and CommandsOptions` classes and the actual implementation of
  the `configure()` function. It also defines the `get()` function, which can be used to
  get the currently used configuration object.

- [`frequenz.repo.config.nox.session`][]: Predefined nox sessions. These are the
  sessions that are used by default.

- [`frequenz.repo.config.nox.util`][]: General purpose utility functions.
"""

from .config import configure

__all__ = [
    "configure",
]
