#!/bin/bash
# Recompile levels.tsv — the player level / souls / ability-point curve — from
# the committed, flattened game data. Commit this output; `git diff` after a
# patch shows curve changes line-by-line.
# redo runs this with cwd = data/; the repo root is one level up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/levels.py" \
  gamedata.flat/scripts/heroes.jsonl

"$py" -m deadlock.levels <gamedata.flat/scripts/heroes.jsonl
