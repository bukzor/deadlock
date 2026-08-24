#!/bin/bash
# Recompile weapons.tsv — each live hero's primary weapon (damage, fire rate,
# clip, reload, range, derived DPS) — from the committed, flattened game data.
# A build-local view, not committed: it derives entirely from gamedata.flat/.
# redo runs this with cwd = data/gamedata.tsv/; the repo root is two levels up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/weapons.py" \
  ../gamedata.flat/scripts/heroes.jsonl \
  ../gamedata.flat/scripts/abilities.jsonl

"$py" -m deadlock.weapons ../gamedata.flat/scripts/abilities.jsonl \
  <../gamedata.flat/scripts/heroes.jsonl
