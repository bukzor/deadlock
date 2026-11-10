#!/bin/bash
# Remove every generated output so the next `redo` rebuilds from scratch:
# - gitignored outputs (extraction, gamedata.json/, manifest, gamedata.list,
#   the per-DLL documents, dlls.list, the check outputs, the cvarlist captures)
#   via git clean, scoped by explicit pathspecs — the provisioned VRF CLI (a
#   51MB download) is deliberately NOT listed; to force a re-provision,
#   `rm -r data/tools/Source2Viewer-CLI*`
# - committed outputs (the TSV views, gamedata's and the DLL store's, the build
#   stamp) via rm; git has them,
#   and rebuilding then reading `git diff` is the whole workflow
# redo-always: `redo clean` never considers itself up to date.
# redo runs this with cwd = repo root.
set -euo pipefail

redo-always

# progress/summaries belong on stderr; stdout is the (empty) target
exec >&2

git clean -fdX -- data/gamedata data/gamedata.json data/gamedata.dense.tsv data/manifest.jsonl \
  data/dlls data/dlls.list data/dlls.check data/cvarlist
rm -vf data/gamedata.list data/deadlock-version.json
find data/gamedata.tsv data/dlls -maxdepth 1 -type f -name '*.tsv' -print0 | xargs -0 -r rm -vf
