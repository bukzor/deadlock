#!/bin/sh
# Recompile item_bonuses.tsv — the passive stat bonuses each shop item grants
# (the "what does it do" companion to items.tsv) — from the committed, flattened
# game data. Commit this output; `git diff` after a patch shows bonus changes
# line-by-line.
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/item_bonuses.py" \
  gamedata.jsonl

"$py" -m deadlock.item_bonuses gamedata.jsonl >"$3"
