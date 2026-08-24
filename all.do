#!/bin/bash
# Build all generated data: the committed diff-friendly artifacts (the VPK
# manifest and one flattened JSONL per game-data file, gamedata.flat/ — the
# !/data/... exceptions in .gitignore) plus the build-local TSV views
# (gamedata.tsv/). `redo all` (or just `redo`) from the repo root regenerates
# them all against the current install. redo runs this with cwd = repo root.
set -euo pipefail

redo-ifchange data/gamedata.list

sed 's#^\./#data/gamedata.flat/#; s#\.vdata$#.jsonl#' data/gamedata.list |
  xargs redo-ifchange \
    data/manifest.jsonl \
    data/gamedata.tsv/levels.tsv \
    data/gamedata.tsv/heroes.tsv \
    data/gamedata.tsv/items.tsv \
    data/gamedata.tsv/abilities.tsv \
    data/gamedata.tsv/weapons.tsv \
    data/gamedata.tsv/item_bonuses.tsv \
    data/gamedata.tsv/ability_upgrades.tsv \
;
