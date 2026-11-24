#!/bin/bash
# The forum CSV: suggested replacement captions for every foreign-language and
# uncaptioned VO line (columns: see bukzor_deadlock.vo_forum). Local
# (gitignored): it holds nothing foreign.tsv and lines.tsv don't.
# redo runs this with cwd = data/vo/.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
names="$("$py" -m bukzor_deadlock.paths hero_names_loc)"

redo-ifchange \
  "$root/src/bukzor_deadlock/vo_forum.py" \
  "$root/src/bukzor_deadlock/vo_asr.py" \
  "$root/src/bukzor_deadlock/loc.py" \
  "$root/src/bukzor_deadlock/dlls_tsv.py" \
  foreign.tsv lines.tsv "$names"
"$py" -m bukzor_deadlock.vo_forum foreign.tsv lines.tsv "$names"
