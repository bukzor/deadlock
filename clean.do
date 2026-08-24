#!/bin/bash
# Remove every generated output so the next `redo` rebuilds from scratch:
# - gitignored outputs (extraction, TSV views, gamedata.list) via git clean,
#   scoped by explicit pathspecs — data/tools/ (the vendored VRF binary,
#   ./bin/fetch-vrf to restore) is deliberately NOT listed
# - committed outputs (manifest, gamedata.flat leaves) via rm; git has them,
#   and rebuilding then reading `git diff` is the whole workflow
# redo-always: `redo clean` never considers itself up to date.
# redo runs this with cwd = repo root.
set -euo pipefail

redo-always

# progress/summaries belong on stderr; stdout is the (empty) target
exec >&2

git clean -fdX -- data/gamedata data/gamedata.tsv
rm -vf data/gamedata.list data/manifest.jsonl
find data/gamedata.flat -name '*.jsonl' -print0 | xargs -0 -r rm -vf
