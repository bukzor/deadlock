#!/bin/bash
# The `boon` demo-parser CLI at its natural path: a symlink into the
# provisioned venv (boon.d -- see that .do), so consumers `redo-ifchange` the
# binary path and get the venv provisioned transitively. The link is relative
# and $3 is a sibling of $1, so it stays valid after redo moves it into place.
# redo runs this with cwd = data/tools/.
set -euo pipefail

redo-ifchange boon.d

ln -s boon.d/bin/boon "$3"
