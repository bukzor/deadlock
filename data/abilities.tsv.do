#!/bin/bash
# Recompile abilities.tsv — each live hero's four signature abilities (type,
# cooldown, charges) — from the committed, flattened game data. Commit this
# output; `git diff` after a patch shows ability changes line-by-line.
# redo runs this with cwd = data/; the repo root is one level up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/abilities.py" \
  gamedata.flat/scripts/heroes.jsonl \
  gamedata.flat/scripts/abilities.jsonl

"$py" -m deadlock.abilities gamedata.flat/scripts/abilities.jsonl \
  <gamedata.flat/scripts/heroes.jsonl
