#!/bin/bash
# usage: docs/dev/probes/winpy_all.sh MODULE >OUT.jsonl
# Run a winpy probe MODULE (copied into trash/winpy/, bin/winpy's cwd) over
# every DLL whose load is `ok`, 4 at a time; one JSON line per DLL on stdout,
# or {"dll", "failed": status} when the probe fails.
set -euo pipefail
cd "$(dirname "$0")/../../.."
py=.venv/bin/python
export probe=$1 WINPY_TIMEOUT=240
mapfile -t bins < <($py -m deadlock.paths bin_dirs)
wb=(); for b in "${bins[@]}"; do wb+=("$(wslpath -w "$b")"); done
export B0=${wb[0]} B1=${wb[1]}
$py -m deadlock.dlls_load --ok data/dlls/load/*.json |
  while read -r n; do
    printf '%s\0' "$(wslpath -w "$($py -m deadlock.dlls_list "$n" <data/dlls.list)")"
  done |
  xargs -0 -P4 -n1 bash -c 'out=$(./bin/winpy "$probe" "$1" "$B0" "$B1" 2>/dev/null) || out="{\"dll\": \"${1##*\\}\", \"failed\": $?}"; printf "%s\n" "$out"' _
