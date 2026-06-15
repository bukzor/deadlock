#!/bin/sh
# Recompile levels.tsv — the player level / souls / ability-point curve — from
# the committed, flattened game data. Commit this output; `git diff` after a
# patch shows curve changes line-by-line.
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/levels.py" \
  gamedata.jsonl

"$py" -m deadlock.levels gamedata.jsonl >"$3"
