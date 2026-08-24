#!/bin/bash
# Regenerate the path-sorted VPK manifest as JSONL (one file per line).
# Local only, never committed: it's a verbatim listing of Valve's archive.
# Useful at the console for spotting which files a patch touched.
# redo runs this with cwd = data/; the repo root is one level up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd .. && pwd)
py="$root/.venv/bin/python"

redo-ifchange \
  "$root/src/deadlock/manifest.py" \
  "$root/src/deadlock/archive.py" \
  "$root/src/deadlock/jsonl.py" \
  "$root/src/deadlock/paths.py" \
  "$root/data/deadlock-version.json"

vpk=$("$py" -m deadlock.paths vpk_dir_file)
redo-ifchange "$vpk"

# already path-sorted by manifest_records; no external sort needed
"$py" -m deadlock.manifest "$vpk"
