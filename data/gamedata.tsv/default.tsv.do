#!/bin/bash
# The committed views, split from the local dense ones (../gamedata.dense.tsv/):
# X.tsv keeps the varying columns; X.defaults.tsv holds each single-valued
# column once, and is absent when there is none (redo deletes an empty target).
# Joined, they are lossless: `python -m deadlock.sparse dense X.tsv X.defaults.tsv`.
# redo runs this with cwd = data/gamedata.tsv/; the repo root is two levels up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
case "$2" in
  *.defaults) mode=defaults; view=${2%.defaults} ;;
  *) mode=sparse; view=$2 ;;
esac
dense=../gamedata.dense.tsv/$view.tsv

redo-ifchange "$root/src/deadlock/sparse.py" "$dense"
"$root/.venv/bin/python" -m deadlock.sparse "$mode" <"$dense"
