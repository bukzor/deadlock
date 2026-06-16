#!/bin/sh
# Recompile ability_upgrades.tsv — what each signature ability's three upgrades
# do (the "what does leveling it do" companion to abilities.tsv) — from the
# committed, flattened game data. Commit this output; `git diff` after a patch
# shows upgrade changes line-by-line.
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/ability_upgrades.py" \
  "$root/src/deadlock/abilities.py" \
  gamedata.jsonl

"$py" -m deadlock.ability_upgrades gamedata.jsonl >"$3"
