#!/bin/bash
# Provision the ValveResourceFormat / Source2Viewer-CLI release named in
# vrf-release.json (the latest upstream release, rechecked daily).
# A directory target (see reference.kb/redo-do-scripts.md): the release ships
# the CLI plus four .so libraries that must sit beside it, and redo can't track
# sibling writes as side effects — so the whole directory is the target.
# The fetch itself lives in bin/fetch-vrf; this only decides when to run it,
# so a new upstream release re-provisions, and everything extracted with the
# CLI re-extracts.
# redo runs this with cwd = data/tools/.
set -euo pipefail

root=$(cd ../.. && pwd)

redo-ifchange "$root/bin/fetch-vrf" vrf-release.json

# progress/summaries belong on stderr; a directory target writes no stdout
exec >&2

"$root/bin/fetch-vrf" vrf-release.json "$3.tmp"

# pre-clear the stale directory so redo's file-oriented $3 -> $1 move doesn't
# nest, keeping the prior good build until the new one is installed
if [ -e "$1" ]; then
  mv "$1" "$1.old"
fi
mv "$3.tmp" "$3"
if [ -e "$1.old" ]; then
  rm -r "$1.old"   # no -f: surface unexpected state loudly
fi
