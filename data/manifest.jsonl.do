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
  "$root/src/bukzor_deadlock/manifest.py" \
  "$root/src/bukzor_deadlock/archive.py" \
  "$root/src/bukzor_deadlock/jsonl.py" \
  "$root/src/bukzor_deadlock/paths.py" \
  "$root/data/deadlock-version.json"

vpk=$("$py" -m bukzor_deadlock.paths vpk_dir_file)
redo-ifchange "$vpk"

# already path-sorted by manifest_records; no external sort needed
"$py" -m bukzor_deadlock.manifest "$vpk"
