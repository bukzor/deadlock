#!/bin/sh
# Build every committed, line-grained leaf data file — the diff-friendly outputs
# tracked in git (mirrors the !/data/... exceptions in .gitignore). `redo all`
# (or just `redo`) from the repo root regenerates them all against the current
# install. redo runs this with cwd = repo root.
set -eu

redo-ifchange \
  data/manifest.jsonl \
  data/gamedata.jsonl \
  data/levels.tsv
