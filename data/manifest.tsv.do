#!/bin/sh
# Regenerate the deterministic VPK manifest (path<TAB>crc32<TAB>size).
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

# rebuild when the parser, path resolution, or the source VPK changes
redo-ifchange \
  "$root/src/deadlock/manifest.py" \
  "$root/src/deadlock/archive.py" \
  "$root/src/deadlock/paths.py"

vpk=$("$py" -c 'from deadlock import paths; print(paths.vpk_dir_file())')
redo-ifchange "$vpk"

"$py" -m deadlock.manifest "$vpk" >"$3"
