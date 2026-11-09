#!/bin/bash
# On-demand check, not part of all.do: tier0's own registry, read back after
# server's and client's Init replayed their queues (bin/winpy dllscan registry),
# against each DLL's convars and concommands documents
# (deadlock.registry_check). The target is the summary of counts, also
# printed on stderr; any mismatch fails it, naming each name.
# docs/dev/cvar-dump.kb/validation.md
# redo runs this with cwd = data/dlls.check/; the repo root is two up.
set -euo pipefail
redo-ifchange ../../bin/winpy-facet.bash
# shellcheck source=../../bin/winpy-facet.bash
. ../../bin/winpy-facet.bash

redo-ifchange "$root/src/deadlock/"{registry_check,dlls_convars,dlls_concommands,dlls_tsv,sparse,types}.py
for name in server.dll client.dll; do
  lookup "$name"
  require_loaded "$name"
  closure "$root/data/dlls/load/$name.json"
  docs=("$root/data/dlls/"{convars,concommands}"/$name.json")
  redo-ifchange "${docs[@]}"
  dllscan registry "$dll" | "$py" -m deadlock.registry_check "${docs[@]}"
done | tee "$3" >&2
