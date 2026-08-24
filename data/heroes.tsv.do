#!/bin/bash
# Recompile heroes.tsv — the wide per-hero base stat sheet — from the committed,
# flattened game data. Commit this output; `git diff` after a patch shows hero
# stat changes (one hero per line).
# redo runs this with cwd = data/; the repo root is one level up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/heroes.py" \
  gamedata.flat/scripts/heroes.jsonl

"$py" -m deadlock.heroes <gamedata.flat/scripts/heroes.jsonl
