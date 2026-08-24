#!/bin/bash
# Recompile item_bonuses.tsv — the passive stat bonuses each shop item grants
# (the "what does it do" companion to items.tsv) — from the committed, flattened
# game data. A build-local view, not committed: it derives entirely from
# gamedata.flat/.
# redo runs this with cwd = data/gamedata.tsv/; the repo root is two levels up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/item_bonuses.py" \
  ../gamedata.flat/scripts/abilities.jsonl

"$py" -m deadlock.item_bonuses <../gamedata.flat/scripts/abilities.jsonl
