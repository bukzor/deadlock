#!/bin/bash
# One facet's aggregate, data/dlls/<facet>.tsv: every DLL's <facet>/<dll>.json
# document as rows, by deadlock.dlls_<facet> (cells: deadlock.dlls_tsv). The
# case table names each facet's DLLs: every one in dlls.list, or for a
# load-time facet only those whose load is ok. Anything unlisted fails loudly
# rather than being silently captured by this default rule.
# redo runs this with cwd = data/dlls/; $2 = the facet; the repo root is two up.
set -euo pipefail

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
src="$root/src/deadlock"
deps=("$src/dlls_$2.py" "$src/dlls_tsv.py" "$src/sparse.py" "$src/types.py" "$root/src/dllscan/document.py")

redo-ifchange ../dlls.list
all=$(sed 's,.*/,,' ../dlls.list)
mapfile -t dlls <<<"$all"

case "$2" in
  file|load) ;;
  concommands)
    loads=("${dlls[@]/#/load/}")
    loads=("${loads[@]/%/.json}")
    redo-ifchange "$src/dlls_load.py" "$src/dlls_tsv.py" "$src/types.py" "${loads[@]}"
    ok=$("$py" -m deadlock.dlls_load --ok "${loads[@]}")
    mapfile -t dlls <<<"$ok" ;;
  *)
    echo "no such facet: $2 (add it to default.tsv.do's table)" >&2; exit 1 ;;
esac

docs=("${dlls[@]/#/$2/}")
docs=("${docs[@]/%/.json}")
redo-ifchange "${deps[@]}" "${docs[@]}"

"$py" -m "deadlock.dlls_$2" "${docs[@]}" >"$3"
redo-stamp <"$3"
