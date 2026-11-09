#!/bin/bash
# Check: the command anchors arrive in their DLL's queue with the flags they
# must have, and engine2, client and server each yield a command queue
# (deadlock.dlls_check concommands, over ../dlls/concommands.tsv). The target
# is the anchor rows, local only. docs/dev/cvar-dump.kb/validation.md
# redo runs this with cwd = data/dlls.check/; the repo root is two up.
set -euo pipefail

root=$(cd ../.. && pwd)
tsv=../dlls/concommands.tsv

redo-ifchange "$root/src/deadlock/"{dlls_check,dlls_tsv,sparse,types}.py "$tsv"
"$root/.venv/bin/python" -m deadlock.dlls_check concommands "$tsv" >"$3"
