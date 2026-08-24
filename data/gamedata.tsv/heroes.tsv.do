#!/bin/bash
# Recompile heroes.tsv — the wide per-hero base stat sheet — from the committed,
# flattened game data. A build-local view, not committed: it derives entirely
# from gamedata.flat/, where the leaf-grain diff lives.
# redo runs this with cwd = data/gamedata.tsv/; the repo root is two levels up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/heroes.py" \
  ../gamedata.flat/scripts/heroes.jsonl

"$py" -m deadlock.heroes <../gamedata.flat/scripts/heroes.jsonl
