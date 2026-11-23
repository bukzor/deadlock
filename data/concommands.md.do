#!/bin/bash
# dlls/concommands.tsv as a Markdown help page, per module, by name
# (bukzor_deadlock.dlls_concommands_md). A reading view, local only.
# redo runs this with cwd = data/; the repo root is one up.
set -euo pipefail

root=$(cd .. && pwd)
redo-ifchange dlls/concommands.tsv "$root/src/bukzor_deadlock/"{dlls_concommands_md,dlls_md,dlls_tsv,sparse}.py
"$root/.venv/bin/python" -m bukzor_deadlock.dlls_concommands_md <dlls/concommands.tsv >"$3"
