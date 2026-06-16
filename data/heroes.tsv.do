#!/bin/sh
# Recompile heroes.tsv — the wide per-hero base stat sheet — from the committed,
# flattened game data. Commit this output; `git diff` after a patch shows hero
# stat changes (one hero per line).
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/heroes.py" \
  gamedata.jsonl

"$py" -m deadlock.heroes gamedata.jsonl >"$3"
