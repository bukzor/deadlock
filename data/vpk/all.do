#!/bin/bash
# Explode every install VPK whole: one data/vpk/<pak>.d per game dir holding
# a pak01_dir.vpk. Opt-in (not part of the repo's `redo all`): see
# docs/dev/decisions.kb/explode-vpks-to-plain-files.md for its cost. Each
# pak refuses to start without room for it (bukzor_deadlock.explode.check_room).
# Consumers depend on the subset they need instead.
# redo runs this with cwd = data/vpk/.
set -euo pipefail

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"

redo-always  # rediscover the paks: a patch can add a locale
"$py" -m bukzor_deadlock.paths pak_dir_files |
  sed 's#^.*/\([^/]*\)/pak01_dir\.vpk$#\1.d#' |
  xargs -d'\n' redo-ifchange
