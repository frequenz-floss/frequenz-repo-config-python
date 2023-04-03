# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Utilities to build noxfiles.

The main entry point is the [`configure()`][configure] function, which will
configure all nox sessions according to some configuration.

You should call `configure()` using one of the default configurations provided
in the [`default`][] module. For example:

```python
from frequenz.repo import config

config.nox.configure(config.nox.default.lib_config)
```

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

- [`config`][]: Low-level utilities to configure nox sessions. It defines the
  `Config` and CommandsOptions` classes and the actual implementation of the
  `configure()` function. It also defines the `get()` function, which can be
  used to get the currently used configuration object.

- [`session`][]: Predefined nox sessions. These are the sessions that are used
  by default.

- [`util`][]: General purpose utility functions.
"""

from . import config, default, session, util
from .config import configure

__all__ = [
    "config",
    "configure",
    "default",
    "session",
    "util",
]
