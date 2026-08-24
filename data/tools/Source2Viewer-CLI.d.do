#!/bin/bash
# Provision the pinned ValveResourceFormat / Source2Viewer-CLI.
# A directory target (see reference.kb/redo-do-scripts.md): the release ships
# the CLI plus four .so libraries that must sit beside it, and redo can't track
# sibling writes as side effects — so the whole directory is the target.
# The fetch itself (and the version/checksum pin) lives in bin/fetch-vrf; this
# only decides when to run it, so bumping the pin re-provisions.
# redo runs this with cwd = data/tools/.
set -euo pipefail

root=$(cd ../.. && pwd)

redo-ifchange "$root/bin/fetch-vrf"

# progress/summaries belong on stderr; a directory target writes no stdout
exec >&2

"$root/bin/fetch-vrf" "$3.tmp"

# pre-clear the stale directory so redo's file-oriented $3 -> $1 move doesn't
# nest, keeping the prior good build until the new one is installed
if [ -e "$1" ]; then
  mv "$1" "$1.old"
fi
mv "$3.tmp" "$3"
if [ -e "$1.old" ]; then
  rm -r "$1.old"   # no -f: surface unexpected state loudly
fi
