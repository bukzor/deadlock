#!/bin/sh
# Extract + decompile the game-data resources (vdata_c -> KV3 text) into
# data/gamedata/, and emit the sorted list of produced files as this target.
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

root=$(cd .. && pwd)
py="$root/.venv/bin/python"
bin="$root/data/tools/Source2Viewer-CLI"
out="$root/data/gamedata"

[ -x "$bin" ] || { echo "Source2Viewer-CLI missing; run ./bin/fetch-vrf" >&2; exit 1; }

redo-ifchange \
  "$root/src/deadlock/extract.py" \
  "$root/src/deadlock/s2v.py" \
  "$root/src/deadlock/paths.py" \
  "$bin"

vpk=$("$py" -c 'from deadlock import paths; print(paths.vpk_dir_file())')
redo-ifchange "$vpk"

# rebuild cleanly so removed assets don't linger
if [ -d "$out" ]; then rm -r "$out"; fi
"$py" -m deadlock.extract "$out" vdata_c

( cd "$out" && find . -type f | sort ) >"$3"
