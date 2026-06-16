#!/bin/sh
# Recompile items.tsv — the shop item economy (tier, resolved soul cost, slot,
# shop filter, components) — from the committed, flattened game data. Commit this
# output; `git diff` after a patch shows item changes line-by-line.
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/items.py" \
  gamedata.jsonl

"$py" -m deadlock.items gamedata.jsonl >"$3"
