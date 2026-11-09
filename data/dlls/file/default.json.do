#!/bin/bash
# One DLL's `file` facet: its size and sha256 on disk, as a FileDocument. Local
# only, never committed (a hash of Valve's bytes; docs/dev/cvar-dump.kb/
# output-views.md). The other facets' atoms share this shape: look the DLL up
# in dlls.list (the guard), depend on it, write one document to $3.
# Guard: $2 must be a basename in dlls.list; anything else fails loudly.
# redo runs this with cwd = data/dlls/file/; $2 = target minus ".json".
set -euo pipefail

root=$(cd ../../.. && pwd)
py="$root/.venv/bin/python"
list="$root/data/dlls.list"

redo-ifchange \
  "$list" \
  "$root/src/deadlock/dlls_list.py" \
  "$root/src/deadlock/paths.py" \
  "$root/src/deadlock/dll_file.py" \
  "$root/src/dllscan/document.py"

dll=$("$py" -m deadlock.dlls_list "$2" <"$list")
redo-ifchange "$dll"

"$py" -m deadlock.dll_file "$dll" >"$3"
redo-stamp <"$3"
