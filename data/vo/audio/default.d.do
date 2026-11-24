#!/bin/bash
# One hero's VO clips as MP3: sounds/vo/<hero>/a/b.vsnd_c from the exploded
# pak lands at <hero>.d/a/b.mp3. VRF -d copies the MP3 the vsnd_c wraps
# (no re-encode; docs/dev/formats.kb/vsnd.md). The whole hero directory, not
# only the ASR's clips: it takes about a second and is also for listening.
# Local (gitignored): Valve audio.
# A directory target (see reference.kb/redo-do-scripts.md).
# redo runs this with cwd = data/vo/audio/.
set -euo pipefail

src=../../vpk/citadel/sounds/vo.d/$2
s2v=../../tools/Source2Viewer-CLI
redo-ifchange ../../vpk/citadel/sounds/vo.d "$s2v"

# a directory target writes no stdout
exec >&2

"$s2v" -i "$src/" --recursive -e vsnd_c -d -q --threads 4 -o "$3.tmp/"

# pre-clear the stale directory so redo's file-oriented $3 -> $1 move doesn't
# nest, keeping the prior good build until the new one is installed
if [ -e "$1" ]; then
  mv "$1" "$1.old"
fi
mv "$3.tmp" "$3"
if [ -e "$1.old" ]; then
  rm -r "$1.old"   # no -f: surface unexpected state loudly
fi
