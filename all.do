#!/bin/bash
# Build all generated data: the committed, transformative TSV views
# (gamedata.tsv/, dlls/<facet>.tsv), the build stamp (deadlock-version.json),
# and the VRF release record (tools/vrf-release.json, rechecked daily), plus the
# local intermediates they derive from (extraction, gamedata.json/,
# manifest.jsonl, the per-DLL documents — gitignored, near-verbatim Valve data),
# and the checks that fail the build if the DLL scan reads garbage
# (dlls.check/). `redo` from the repo root regenerates everything against the
# current install; then read `git diff`.
# redo runs this with cwd = repo root.
set -euo pipefail

views=(levels heroes items abilities ability_profiles item_bonuses ability_upgrades)
committed=(data/deadlock-version.json data/tools/vrf-release.json)
# each view is a sparse X.tsv plus its X.defaults.tsv (absent when empty)
for view in "${views[@]}"; do
  committed+=("data/gamedata.tsv/$view.tsv" "data/gamedata.tsv/$view.defaults.tsv")
done
for facet in file load concommands convars; do
  committed+=("data/dlls/$facet.tsv")
done

# A fresh clone's committed outputs came from git, not from redo, so redo would
# treat them as hand-written and skip them (silently, exiting 0). Adopting says
# "these are mine": redo rebuilds them when their dependencies change, and
# leaves them alone when they don't — unlike deleting them, which forfeits
# incrementality and destroys the outputs if the build then fails.
redo-adopt "${committed[@]}"

redo-ifchange data/gamedata.list

sed 's#^\./#data/gamedata.json/#; s#\.vdata$#.json#' data/gamedata.list |
  xargs redo-ifchange \
    data/manifest.jsonl \
    data/dlls.check/strides \
    data/dlls.check/concommands \
    data/dlls.check/convars \
    "${committed[@]}" \
;
