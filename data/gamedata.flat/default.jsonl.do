#!/bin/bash
# Flatten one decompiled vdata file into sorted JSONL leaves — one target per
# source file, so a patch re-flattens only the files it touched and `redo -j`
# parallelizes across them. Local only, never committed: this is near-verbatim
# Valve data (see decisions.kb/commit-diffable-data-let-git-diff.md).
# Guard: buildable iff the matching source vdata exists; anything else fails
# loudly rather than being silently captured by this default rule.
# redo runs this with cwd = data/gamedata.flat/; $2 = target minus ".jsonl".
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
src="$root/data/gamedata/$2.vdata"

[[ -f "$src" ]] || { echo "no such game data: $2.vdata (run: redo data/gamedata.list)" >&2; exit 1; }

redo-ifchange \
  "$root/data/deadlock-version.json" \
  "$root/src/deadlock/gamedata.py" \
  "$root/src/deadlock/flatten.py" \
  "$root/src/deadlock/jsonl.py" \
  "$root/src/deadlock/kv3.py" \
  "$root/src/deadlock/kv3text.py" \
  "$root/src/deadlock/types.py" \
  "$src"

# redo doesn't create target subdirectories
mkdir -p "$(dirname "$1")"

# pre-sorted per file: stable, diff-friendly ordering
"$py" -m deadlock.gamedata <"$src" | LC_ALL=C sort
