#!/bin/bash
# Recompile ability_upgrades.tsv — what each signature ability's three upgrades
# do (the "what does leveling it do" companion to abilities.tsv) — from the
# committed, flattened game data. Commit this output; `git diff` after a patch
# shows upgrade changes line-by-line.
# redo runs this with cwd = data/; the repo root is one level up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/ability_upgrades.py" \
  "$root/src/deadlock/abilities.py" \
  gamedata.flat/scripts/heroes.jsonl \
  gamedata.flat/scripts/abilities.jsonl

"$py" -m deadlock.ability_upgrades gamedata.flat/scripts/heroes.jsonl \
  <gamedata.flat/scripts/abilities.jsonl
