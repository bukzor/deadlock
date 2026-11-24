#!/bin/bash
# The caption mod: ./captions.d/tree packed as one VPK v2, its data inline in
# the one file, the format deadlock-mod-manager's own writer makes. Install
# it with the manager's "Add Local Mod" (docs/dev/formats.kb/caption-mod.md).
# Local (gitignored), like everything it is built from.
# redo runs this with cwd = data/mod/.
set -euo pipefail

root=$(cd ../.. && pwd)
vpk="$root/.venv/bin/vpk"

redo-ifchange captions.d

# vpk writes the file itself; stdout is for progress only
exec >&2

"$vpk" -cv 2 -c captions.d/tree "$3"
"$vpk" -t "$3"
