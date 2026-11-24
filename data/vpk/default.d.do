#!/bin/bash
# Explode raw files out of one install VPK, byte for byte (no decompiling).
#   data/vpk/<pak>.d            the whole pak            (redo data/vpk/core.d)
#   data/vpk/<pak>/<dir>.d      the pak's directory <dir> (data/vpk/citadel/sounds/vo.d)
# <pak> is a game dir holding pak01_dir.vpk: citadel, core, citadel_<lang>.
# The target directory mirrors its VPK directory: <dir>/a/b.ext lands at
# <dir>.d/a/b.ext. Paks are never merged; overlay order is the consumer's call.
# Rebuilt when the pak's index or the code changes.
# A directory target (see reference.kb/redo-do-scripts.md).
# redo runs this with cwd = data/vpk/.
set -euo pipefail

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"

pak=${2%%/*}
dir=${2#"$pak"}
dir=${dir#/}

redo-ifchange \
  "$root/src/bukzor_deadlock/explode.py" \
  "$root/src/bukzor_deadlock/archive.py"

vpk="$("$py" -m bukzor_deadlock.paths game_dir)/$pak/pak01_dir.vpk"
redo-ifchange "$vpk"

# a directory target writes no stdout
exec >&2

mkdir -p "$(dirname "$3")"
"$py" -m bukzor_deadlock.explode "$vpk" "$3.tmp" ${dir:+"$dir"}

# pre-clear the stale directory so redo's file-oriented $3 -> $1 move doesn't
# nest, keeping the prior good build until the new one is installed
if [ -e "$1" ]; then
  mv "$1" "$1.old"
fi
mv "$3.tmp" "$3"
if [ -e "$1.old" ]; then
  rm -r "$1.old"   # no -f: surface unexpected state loudly
fi
