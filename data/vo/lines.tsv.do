#!/bin/bash
# One row per hero VO clip: hero, event, vsnd, crc32, english (columns: see
# bukzor_deadlock.vo_lines). Committed: the transformative join that keys
# per-clip work (transcripts) by the audio's CRC32. Other locales' captions
# are ./captions.tsv, joined on event.
# redo runs this with cwd = data/vo/.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
english="$("$py" -m bukzor_deadlock.paths citadel_dir)/resource/localization/citadel_generated_vo/citadel_generated_vo_english.txt"
sounds=../vpk/citadel/sounds/vo.d

redo-ifchange \
  "$root/src/bukzor_deadlock/vo_lines.py" \
  "$root/src/bukzor_deadlock/vo_soundevents.py" \
  "$root/src/bukzor_deadlock/vo_captions.py" \
  "$root/src/bukzor_deadlock/kv3text.py" \
  soundevents.d "$sounds" "$english"
"$py" -m bukzor_deadlock.vo_lines soundevents.d "$sounds" "$english"
