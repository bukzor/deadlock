#!/bin/bash
# Every VO caption in every locale, long: event, lang, caption (columns: see
# bukzor_deadlock.vo_captions). Read in place from the install's loose
# caption files, not the paks (docs/dev/formats.kb/vo-captions.md).
# Local (gitignored): it is the caption files re-encoded, near-verbatim
# Valve text, ~75 MB. Join it to ./lines.tsv on event.
# redo runs this with cwd = data/vo/.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
captions="$("$py" -m bukzor_deadlock.paths citadel_dir)/resource/localization/citadel_generated_vo"

redo-ifchange "$root/src/bukzor_deadlock/vo_captions.py" "$captions"
find "$captions" -name 'citadel_generated_vo_*.txt' -print0 | xargs -r0 redo-ifchange
"$py" -m bukzor_deadlock.vo_captions "$captions"
