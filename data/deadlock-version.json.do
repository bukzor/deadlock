#!/bin/bash
# Reparse the install's steam.inf into one-key-per-line JSON: which game build
# produced the committed views. Committed, and depended on by every target that
# reads the game install, so a patch bump invalidates them (in addition to the
# VPK dep, which catches content changes that don't bump the version).
# redo runs this with cwd = data/; the repo root is one level up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/version.py" \
  "$root/src/deadlock/paths.py"

inf=$("$py" -c 'from deadlock import paths; print(paths.steam_inf())')
redo-ifchange "$inf"

"$py" -m deadlock.version <"$inf"
