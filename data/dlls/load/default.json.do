#!/bin/bash
# One DLL's `load` facet: loaded in a fresh Windows process (bin/winpy dllscan
# load), what the load added (`ok`) or why it was refused (`failed`). A DLL in
# deadlock.dll_load.EXCLUDED is never loaded: it gets its `excluded` record,
# written here. A timeout (winpy exit 124) fails the build; the fix is a new
# exclusion. Shape and guard as data/dlls/file/default.json.do; the shared
# steps are in bin/winpy-facet.bash.
# redo runs this with cwd = data/dlls/load/; $2 = target minus ".json".
set -euo pipefail
redo-ifchange ../../../bin/winpy-facet.bash
# shellcheck source=../../../bin/winpy-facet.bash
. ../../../bin/winpy-facet.bash

lookup "$2"
"$py" -m deadlock.dll_load excluded "$2" >"$3"
if [[ ! -s $3 ]]; then
  dllscan load "$dll" >"$3"
  closure "$3"
fi
redo-stamp <"$3"
