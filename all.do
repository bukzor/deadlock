#!/bin/bash
# Build all generated data: the committed, transformative TSV views
# (gamedata.tsv/) and the build stamp (deadlock-version.json), plus the local
# intermediates they derive from (extraction, gamedata.flat/, manifest.jsonl —
# gitignored, near-verbatim Valve data). `redo` from the repo root regenerates
# everything against the current install; then read `git diff`.
# redo runs this with cwd = repo root.
set -euo pipefail

committed=(
  data/deadlock-version.json
  data/gamedata.tsv/levels.tsv
  data/gamedata.tsv/heroes.tsv
  data/gamedata.tsv/items.tsv
  data/gamedata.tsv/abilities.tsv
  data/gamedata.tsv/weapons.tsv
  data/gamedata.tsv/item_bonuses.tsv
  data/gamedata.tsv/ability_upgrades.tsv
)

# A fresh clone's committed outputs came from git, not from redo, so redo would
# treat them as hand-written and skip them (silently, exiting 0). Adopting says
# "these are mine": redo rebuilds them when their dependencies change, and
# leaves them alone when they don't — unlike deleting them, which forfeits
# incrementality and destroys the outputs if the build then fails.
redo-adopt "${committed[@]}"

redo-ifchange data/gamedata.list

sed 's#^\./#data/gamedata.flat/#; s#\.vdata$#.jsonl#' data/gamedata.list |
  xargs redo-ifchange \
    data/manifest.jsonl \
    "${committed[@]}" \
;
