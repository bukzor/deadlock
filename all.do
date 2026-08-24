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

# redo refuses to overwrite a target it didn't generate ("exists and not marked
# as generated"), which would silently leave the committed outputs stale in a
# fresh clone. Dropping them first hands ownership back to redo; they recompile
# from the local flats in seconds, so the expensive steps stay incremental.
rm -f "${committed[@]}"

redo-ifchange data/gamedata.list

sed 's#^\./#data/gamedata.flat/#; s#\.vdata$#.jsonl#' data/gamedata.list |
  xargs redo-ifchange \
    data/manifest.jsonl \
    "${committed[@]}" \
;
