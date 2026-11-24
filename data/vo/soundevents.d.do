#!/bin/bash
# Every VO soundevents file, decompiled by VRF to KV3 text: soundevents/vo/X.vsndevts_c
# from ../vpk/citadel/soundevents/vo.d lands at soundevents.d/X.vsndevts.
# Local (gitignored): near-verbatim Valve data; ./lines.tsv is the committed view.
# A directory target (see reference.kb/redo-do-scripts.md).
# redo runs this with cwd = data/vo/.
set -euo pipefail

src=../vpk/citadel/soundevents/vo.d
s2v=../tools/Source2Viewer-CLI
redo-ifchange "$src" "$s2v"

# a directory target writes no stdout
exec >&2

"$s2v" -i "$src/" -e vsndevts_c -d -q -o "$3.tmp/"

# pre-clear the stale directory so redo's file-oriented $3 -> $1 move doesn't
# nest, keeping the prior good build until the new one is installed
if [ -e "$1" ]; then
  mv "$1" "$1.old"
fi
mv "$3.tmp" "$3"
if [ -e "$1.old" ]; then
  rm -r "$1.old"   # no -f: surface unexpected state loudly
fi
