#!/bin/bash
# The Japanese VO lines with their best English-reader text: hero, event,
# vsnd, replacement, translation, source (columns: see
# bukzor_deadlock.vo_asr_view). Committed: the file to read. Joins ./lines.tsv
# with the committed ML ledgers, transcripts/asr/<hero>.tsv and
# transcripts/fixups.tsv (which may not exist yet); redo never writes those
# (docs/dev/decisions.kb/ml-observations-are-committed-ledgers.md).
# redo runs this with cwd = data/vo/.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
asr=$root/transcripts/asr
fixups=$root/transcripts/fixups.tsv

redo-ifchange \
  "$root/src/bukzor_deadlock/vo_asr_view.py" \
  "$root/src/bukzor_deadlock/vo_asr.py" \
  "$root/src/bukzor_deadlock/vo_asr_ledger.py" \
  "$root/src/bukzor_deadlock/dlls_tsv.py" \
  lines.tsv "$asr"
find "$asr" -name '*.tsv' -print0 | xargs -r0 redo-ifchange
if [ -e "$fixups" ]; then
  redo-ifchange "$fixups"
else
  redo-ifcreate "$fixups"
fi
"$py" -m bukzor_deadlock.vo_asr_view lines.tsv "$asr" "$fixups"
