#!/bin/sh
# Recompile abilities.tsv — each live hero's four signature abilities (type,
# cooldown, charges) — from the committed, flattened game data. Commit this
# output; `git diff` after a patch shows ability changes line-by-line.
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/abilities.py" \
  gamedata.jsonl

"$py" -m deadlock.abilities gamedata.jsonl >"$3"
