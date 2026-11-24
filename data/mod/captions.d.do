#!/bin/bash
# The caption mod's text files, from ../vo/foreign.tsv: tree/ is the VPK's
# tree (tokens-only caption files, one per real locale) and diffs/ holds a
# unified diff per locale for Valve (layout: see bukzor_deadlock.vo_mod and
# docs/dev/formats.kb/caption-mod.md). Every file is parsed back and checked
# as it is written. Local (gitignored): it embeds Valve text (the diffs'
# context) and nothing foreign.tsv doesn't.
# A directory target (see reference.kb/redo-do-scripts.md).
# redo runs this with cwd = data/mod/.
set -euo pipefail

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
src="$root/src/bukzor_deadlock"
captions="$("$py" -m bukzor_deadlock.paths citadel_dir)/resource/localization/citadel_generated_vo"
translations=$root/transcripts/locale-translations.tsv

redo-ifchange \
  "$src/vo_mod.py" "$src/vo_captions.py" "$src/vo_asr.py" \
  "$src/vo_forum.py" "$src/dlls_tsv.py" \
  ../vo/foreign.tsv ../vo/lines.tsv "$captions"
find "$captions" -name 'citadel_generated_vo_*.txt' -print0 | xargs -r0 redo-ifchange
if [ -e "$translations" ]; then
  redo-ifchange "$translations"
else
  redo-ifcreate "$translations"
fi

# a directory target writes no stdout
exec >&2

"$py" -m bukzor_deadlock.vo_mod \
  "$captions" ../vo/foreign.tsv ../vo/lines.tsv "$translations" "$3.tmp"

# pre-clear the stale directory so redo's file-oriented $3 -> $1 move doesn't
# nest, keeping the prior good build until the new one is installed
if [ -e "$1" ]; then
  mv "$1" "$1.old"
fi
mv "$3.tmp" "$3"
if [ -e "$1.old" ]; then
  rm -r "$1.old"   # no -f: surface unexpected state loudly
fi
