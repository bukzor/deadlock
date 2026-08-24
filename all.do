#!/bin/bash
# Build every committed, line-grained leaf data file — the diff-friendly outputs
# tracked in git (mirrors the !/data/... exceptions in .gitignore): the VPK
# manifest, one flattened JSONL per game-data file (gamedata.flat/), and the
# derived TSV views. `redo all` (or just `redo`) from the repo root regenerates
# them all against the current install. redo runs this with cwd = repo root.
set -euo pipefail

redo-ifchange data/gamedata.list

sed 's#^\./#data/gamedata.flat/#; s#\.vdata$#.jsonl#' data/gamedata.list |
  xargs redo-ifchange \
    data/manifest.jsonl \
    data/levels.tsv \
    data/heroes.tsv \
    data/items.tsv \
    data/abilities.tsv \
    data/weapons.tsv \
    data/item_bonuses.tsv \
    data/ability_upgrades.tsv \
;
