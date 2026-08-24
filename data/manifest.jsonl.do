#!/bin/bash
# Regenerate the path-sorted VPK manifest as JSONL (one file per line).
# Commit this output; `git diff` after a patch shows exactly what changed.
# redo runs this with cwd = data/; the repo root is one level up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/manifest.py" \
  "$root/src/deadlock/archive.py" \
  "$root/src/deadlock/jsonl.py" \
  "$root/src/deadlock/paths.py"

vpk=$("$py" -c 'from deadlock import paths; print(paths.vpk_dir_file())')
redo-ifchange "$vpk"

# already path-sorted by manifest_records; no external sort needed
"$py" -m deadlock.manifest "$vpk"
