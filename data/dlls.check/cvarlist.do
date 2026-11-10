#!/bin/bash
# On-demand check, not part of all.do: the engine's own `cvarlist`, captured
# on a dedicated server and on a client (../cvarlist/<side>.log, each a fresh
# launch of the game), against the store's declarations (../dlls/convars.tsv,
# ../dlls/concommands.tsv) and the install's gameinfo.gi overrides
# (deadlock.cvarlist_check). The target is the summary of counts, also printed
# on stderr; any mismatch fails it, naming each name.
# docs/dev/cvar-dump.kb/validation.md
# redo runs this with cwd = data/dlls.check/; the repo root is two up.
set -euo pipefail

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
gameinfo="$("$py" -m deadlock.paths citadel_dir)/gameinfo.gi"
tsvs=(../dlls/convars.tsv ../dlls/concommands.tsv)

redo-ifchange "$root/src/deadlock/"{cvarlist,cvarlist_check,dlls_concommands,dlls_convars,dlls_tsv,registry_check,paths,sparse,types}.py \
  "$gameinfo" "${tsvs[@]}"
# one side at a time: a capture refuses to launch while deadlock.exe runs
for side in server client; do
  redo-ifchange "../cvarlist/$side.log"
  "$py" -m deadlock.cvarlist_check "../cvarlist/$side.log" "$gameinfo" "${tsvs[@]}"
done | tee "$3" >&2
