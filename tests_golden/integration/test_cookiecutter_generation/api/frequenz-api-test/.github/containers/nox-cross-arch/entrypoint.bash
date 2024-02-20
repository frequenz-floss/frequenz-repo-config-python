#!/bin/bash
# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH
set -e

echo "System details:" $(uname -a)
echo "Machine:" $(uname -m)

exec "$@"
