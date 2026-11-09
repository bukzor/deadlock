# shellcheck shell=bash
# The steps shared by the Windows-side facets' atoms,
# data/dlls/{load,concommands,convars}/default.json.do. Each atom sources this
# after `redo-ifchange`-ing it. Each step declares the dependencies it uses, so
# an atom depends on the scanner only if it runs `dllscan` (an excluded DLL's
# `load` atom never does).

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
py="$root/.venv/bin/python"

# The guard: NAME must be a basename in dlls.list; sets `dll` to its path.
# Also declares deadlock.dll_load, which each atom's own guard step runs.
lookup() {
  local list="$root/data/dlls.list"
  redo-ifchange "$list" "$root/src/deadlock/"{dlls_list,paths,dll_load,types}.py \
    "$root/src/dllscan/document.py"
  dll=$("$py" -m deadlock.dlls_list "$1" <"$list")
}

# A load-time facet's guard: load/NAME.json must say `ok`. Any other outcome
# fails loudly, naming it.
require_loaded() {
  local load="$root/data/dlls/load/$1.json"
  redo-ifchange "$load"
  "$py" -m deadlock.dll_load ok "$load"
}

# Print FACET's document for the DLL at DLL: `bin/winpy dllscan FACET`, given
# the Windows paths of the DLL and the bin dirs.
dllscan() {
  local facet=$1 dll=$2 f path bins scanner=() args=()
  for f in "$root"/src/dllscan/*.py; do
    [[ $f == *_test.py ]] || scanner+=("$f")
  done
  redo-ifchange "$dll" "$root/bin/winpy" "${scanner[@]}"
  bins=$("$py" -m deadlock.paths bin_dirs)
  mapfile -t bins <<<"$bins"
  for path in "$dll" "${bins[@]}"; do
    args+=("$(wslpath -w "$path")")
  done
  "$root/bin/winpy" dllscan "$facet" "${args[@]}"
}
