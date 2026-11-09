#!/bin/bash
# One DLL's `convars` facet: its convar reg-list queue, decoded in a fresh
# Windows process (bin/winpy dllscan convars). A load-time facet: the
# guard is the basename in dlls.list *and* load/$2.json saying `ok`; any other
# outcome fails loudly, naming it. Shape as data/dlls/file/default.json.do.
# redo runs this with cwd = data/dlls/convars/; $2 = target minus ".json".
set -euo pipefail

root=$(cd ../../.. && pwd)
py="$root/.venv/bin/python"
list="$root/data/dlls.list"
load="../load/$2.json"

redo-ifchange "$list" "$root/src/deadlock/"{dlls_list,paths,dll_load,types}.py \
  "$root/src/dllscan/document.py"
dll=$("$py" -m deadlock.dlls_list "$2" <"$list")
redo-ifchange "$load"
"$py" -m deadlock.dll_load ok "$load"

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
"$root/bin/winpy" dllscan convars "${args[@]}" >"$3"
redo-stamp <"$3"
