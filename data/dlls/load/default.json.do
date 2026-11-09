#!/bin/bash
# One DLL's `load` facet: loaded in a fresh Windows process (bin/winpy dllscan
# load), what the load added (`ok`) or why it was refused (`failed`). A DLL in
# deadlock.dll_load.EXCLUDED is never loaded: it gets its `excluded` record,
# written here. A timeout (winpy exit 124) fails the build; the fix is a new
# exclusion. Shape and guard as data/dlls/file/default.json.do.
# redo runs this with cwd = data/dlls/load/; $2 = target minus ".json".
set -euo pipefail

root=$(cd ../../.. && pwd)
py="$root/.venv/bin/python"
list="$root/data/dlls.list"

redo-ifchange "$list" "$root/src/deadlock/"{dlls_list,paths,dll_load,types}.py \
  "$root/src/dllscan/document.py"
dll=$("$py" -m deadlock.dlls_list "$2" <"$list")

"$py" -m deadlock.dll_load excluded "$2" >"$3"
if [[ ! -s $3 ]]; then
  scanner=()
  for f in "$root"/src/dllscan/*.py; do
    [[ $f == *_test.py ]] || scanner+=("$f")
  done
  redo-ifchange "$dll" "$root/bin/winpy" "${scanner[@]}"
  bins=$("$py" -m deadlock.paths bin_dirs)
  mapfile -t bins <<<"$bins"
  args=()
  for path in "$dll" "${bins[@]}"; do
    args+=("$(wslpath -w "$path")")
  done
  "$root/bin/winpy" dllscan load "${args[@]}" >"$3"
fi
redo-stamp <"$3"
