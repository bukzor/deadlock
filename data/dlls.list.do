#!/bin/bash
# List every DLL under the install's game/ dir (membership only; see
# deadlock.dll_inventory). Every per-DLL target depends on this list, so it is
# stamped: a rebuild with the same content doesn't re-run them.
# It depends on the build stamp, not on a walk every run (redo-always: ~4 s over
# /mnt/c per build): only a patch adds, removes or renames a DLL, and a patch
# bumps the stamp.
# redo runs this with cwd = data/; the repo root is one level up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/dll_inventory.py" \
  "$root/src/deadlock/paths.py" \
  "$root/data/deadlock-version.json"

"$py" -m deadlock.dll_inventory
