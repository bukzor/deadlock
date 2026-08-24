#!/bin/bash
# Recompile items.tsv — the shop item economy (tier, resolved soul cost, slot,
# shop filter, components) — from the committed, flattened game data. A build-
# local view, not committed: it derives entirely from gamedata.flat/.
# redo runs this with cwd = data/gamedata.tsv/; the repo root is two levels up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/items.py" \
  ../gamedata.flat/scripts/abilities.jsonl \
  ../gamedata.flat/scripts/generic_data.jsonl

"$py" -m deadlock.items ../gamedata.flat/scripts/generic_data.jsonl \
  <../gamedata.flat/scripts/abilities.jsonl
