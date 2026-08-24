#!/bin/bash
# Remove every generated output so the next `redo` rebuilds from scratch:
# - gitignored outputs (extraction, gamedata.flat/, manifest, gamedata.list)
#   via git clean, scoped by explicit pathspecs — the provisioned VRF CLI
#   (a 51MB download) is deliberately NOT listed; to force a re-provision,
#   `rm -r data/tools/Source2Viewer-CLI*`
# - committed outputs (the TSV views, the build stamp) via rm; git has them,
#   and rebuilding then reading `git diff` is the whole workflow
# redo-always: `redo clean` never considers itself up to date.
# redo runs this with cwd = repo root.
set -euo pipefail

redo-always

# progress/summaries belong on stderr; stdout is the (empty) target
exec >&2

git clean -fdX -- data/gamedata data/gamedata.flat data/manifest.jsonl
rm -vf data/gamedata.list data/deadlock-version.json
find data/gamedata.tsv -name '*.tsv' -print0 | xargs -0 -r rm -vf
