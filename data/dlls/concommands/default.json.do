#!/bin/bash
# One DLL's `concommands` facet: its command reg-list queue, decoded in a fresh
# Windows process (bin/winpy dllscan concommands). A load-time facet: the
# guard is the basename in dlls.list *and* load/$2.json saying `ok`. Shape as
# data/dlls/file/default.json.do; the shared steps are in
# bin/winpy-facet.bash.
# redo runs this with cwd = data/dlls/concommands/; $2 = target minus ".json".
set -euo pipefail
redo-ifchange ../../../bin/winpy-facet.bash
# shellcheck source=../../../bin/winpy-facet.bash
. ../../../bin/winpy-facet.bash

lookup "$2"
require_loaded "$2"
closure "../load/$2.json"
dllscan concommands "$dll" >"$3"
redo-stamp <"$3"
