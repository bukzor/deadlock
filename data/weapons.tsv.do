#!/bin/sh
# Recompile weapons.tsv — each live hero's primary weapon (damage, fire rate,
# clip, reload, range, derived DPS) — from the committed, flattened game data.
# Commit this output; `git diff` after a patch shows weapon changes line-by-line.
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/weapons.py" \
  gamedata.jsonl

"$py" -m deadlock.weapons gamedata.jsonl >"$3"
