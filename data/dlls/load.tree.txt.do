#!/bin/bash
# load.tsv drawn as a tree(1)-style forest of who loads whom, edges inferred
# from the load closures (deadlock.dlls_load_tree). A reading view, local only.
# redo runs this with cwd = data/dlls/; the repo root is two up.
set -euo pipefail

root=$(cd ../.. && pwd)
redo-ifchange load.tsv "$root/src/deadlock/"{dlls_load_tree,dlls_tsv,sparse}.py
"$root/.venv/bin/python" -m deadlock.dlls_load_tree <load.tsv >"$3"
