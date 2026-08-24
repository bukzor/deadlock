#!/bin/sh
# Flatten one decompiled vdata file into sorted JSONL leaves — one intermediate
# per source file, so a patch re-flattens only the files it touched and
# `redo -j` parallelizes across them. gamedata.jsonl.do merges these.
# Guard: buildable iff the matching source vdata exists; anything else fails
# loudly rather than being silently captured by this default rule.
# redo runs this with cwd = data/gamedata.flat/; $2 = target minus ".jsonl".
set -eu

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
src="$root/data/gamedata/$2.vdata"

[ -f "$src" ] || { echo "no such game data: $2.vdata (run: redo data/gamedata.list)" >&2; exit 1; }

redo-ifchange \
  "$root/src/deadlock/gamedata.py" \
  "$root/src/deadlock/flatten.py" \
  "$root/src/deadlock/jsonl.py" \
  "$root/src/deadlock/kv3.py" \
  "$root/src/deadlock/kv3text.py" \
  "$root/src/deadlock/types.py" \
  "$src"

# $3 is relative to gamedata.flat/; make it absolute before changing directory,
# and create the target's subdirectory (redo doesn't)
out=$3
case "$out" in /*) ;; *) out="$PWD/$out" ;; esac
mkdir -p "$(dirname "$out")"

# run from inside gamedata/ so the file label is relative (scripts/heroes.vdata);
# pre-sorted per file so the combiner can merge (sort -m) instead of re-sorting
cd "$root/data/gamedata"
"$py" -m deadlock.gamedata "$2.vdata" | LC_ALL=C sort >"$out"
