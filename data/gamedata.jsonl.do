#!/bin/sh
# Combine every decompiled game-data file into one JSONL stream: one record per
# top-level entry (one hero/ability/... per line), tagged with _file and _key.
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/gamedata.py" \
  "$root/src/deadlock/jsonl.py" \
  "$root/src/deadlock/kv3.py" \
  "$root/src/deadlock/types.py" \
  gamedata.list

# $3 is relative to data/; make it absolute before changing directory
out=$3
case "$out" in /*) ;; *) out="$PWD/$out" ;; esac

# load from inside gamedata/ so _file labels are relative (scripts/heroes.vdata)
cd "$root/data/gamedata"
find . -name '*.vdata' | sort | sed 's#^\./##' | xargs "$py" -m deadlock.gamedata >"$out"
