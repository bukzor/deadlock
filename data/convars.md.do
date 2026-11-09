#!/bin/bash
# dlls/convars.tsv as a Markdown help page, per module, by name
# (deadlock.dlls_convars_md). A reading view, local only.
# redo runs this with cwd = data/; the repo root is one up.
set -euo pipefail

root=$(cd .. && pwd)
redo-ifchange dlls/convars.tsv "$root/src/deadlock/"{dlls_convars_md,dlls_md,dlls_tsv,sparse}.py
"$root/.venv/bin/python" -m deadlock.dlls_convars_md <dlls/convars.tsv >"$3"
