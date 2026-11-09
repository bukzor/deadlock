#!/bin/bash
# Check: the convar anchor arrives in its DLL's queue with the flags it must
# have, and engine2, client and server each yield a convar queue
# (deadlock.dlls_check convars, over ../dlls/convars.tsv). The target is the
# anchor rows, local only. docs/dev/cvar-dump.kb/validation.md
# redo runs this with cwd = data/dlls.check/; the repo root is two up.
set -euo pipefail

root=$(cd ../.. && pwd)
tsv=../dlls/convars.tsv

redo-ifchange "$root/src/deadlock/"{dlls_check,dlls_tsv,sparse,types}.py "$tsv"
"$root/.venv/bin/python" -m deadlock.dlls_check convars "$tsv" >"$3"
