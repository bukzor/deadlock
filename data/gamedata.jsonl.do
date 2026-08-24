#!/bin/sh
# Combine every decompiled game-data file into one JSONL stream at leaf grain:
# one scalar per line ({file, path, value}), sorted so a balance patch shows up
# in `git diff` as exactly the lines that changed. Commit this output.
# The per-file flattening lives in gamedata.flat/default.jsonl.do; this target
# fans out to those intermediates and merges them (they arrive pre-sorted).
# redo runs this with cwd = data/; the repo root is one level up.
set -eu

redo-ifchange gamedata.list

targets=$(sed 's#^\./##; s#\.vdata$#.jsonl#; s#^#gamedata.flat/#' gamedata.list)
redo-ifchange $targets

LC_ALL=C sort -m $targets >"$3"
