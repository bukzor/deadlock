#!/bin/bash
# concommands.tsv as a Markdown help page, per module, by name
# (deadlock.dlls_concommands_md). A reading view, local only.
# redo runs this with cwd = data/dlls/; the repo root is two up.
set -euo pipefail

root=$(cd ../.. && pwd)
redo-ifchange concommands.tsv "$root/src/deadlock/"{dlls_concommands_md,dlls_tsv,sparse}.py
"$root/.venv/bin/python" -m deadlock.dlls_concommands_md <concommands.tsv >"$3"
