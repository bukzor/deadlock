#!/bin/bash
# Extract + decompile the game-data resources (vdata_c -> KV3 text) into
# data/gamedata/, and emit the sorted list of produced files as this target.
# redo runs this with cwd = data/; the repo root is one level up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd .. && pwd)
py="$root/.venv/bin/python"
out="$root/data/gamedata"

# depending on the CLI provisions the pinned VRF on demand
redo-ifchange \
  "$root/src/deadlock/extract.py" \
  "$root/src/deadlock/s2v.py" \
  "$root/src/deadlock/paths.py" \
  "$root/data/deadlock-version.json" \
  "$root/data/tools/Source2Viewer-CLI"

vpk=$("$py" -c 'from deadlock import paths; print(paths.vpk_dir_file())')
redo-ifchange "$vpk"

# rebuild cleanly so removed assets don't linger, in gamedata/ and in the
# committed flattened mirror (every flat rebuilds after extraction anyway)
if [[ -d "$out" ]]; then rm -r "$out"; fi
find gamedata.flat -name '*.jsonl' -delete
"$py" -m deadlock.extract "$out" vdata_c

( cd "$out" && find . -type f | sort )
