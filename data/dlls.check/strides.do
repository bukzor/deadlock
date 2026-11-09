#!/bin/bash
# Check: server.dll's reg-list strides, re-learned (bin/winpy dllscan strides),
# still equal the pinned ones, and its anchors label each kind's queue
# (deadlock.dlls_check strides). Either failing fails the build: every
# load-time facet reads the queues at those strides. On success, the target
# is the labelled strides, local only. docs/dev/convar-dump.kb/validation.md
# redo runs this with cwd = data/dlls.check/; the repo root is two up.
set -euo pipefail

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
list="$root/data/dlls.list"

redo-ifchange "$list" "$root/src/deadlock/"{dlls_list,dlls_check,dlls_tsv,paths,sparse,types}.py
dll=$("$py" -m deadlock.dlls_list server.dll <"$list")

scanner=()
for f in "$root"/src/dllscan/*.py; do
  [[ $f == *_test.py ]] || scanner+=("$f")
done
redo-ifchange "$dll" "$root/bin/winpy" "${scanner[@]}"
bins=$("$py" -m deadlock.paths bin_dirs)
mapfile -t bins <<<"$bins"
args=()
for path in "$dll" "${bins[@]}"; do
  args+=("$(wslpath -w "$path")")
done
"$root/bin/winpy" dllscan strides "${args[@]}" >"$3"
"$py" -m deadlock.dlls_check strides "$3"
