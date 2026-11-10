#!/bin/bash
# The engine's own `cvarlist` for one side, server or client: a launch of the
# installed game (bin/cvarlist-capture), on demand only (dlls.check/cvarlist.do).
# Gitignored: Valve data, and the client's values are the user's.
# It relaunches only when an input changes: the DLLs (../dlls/file.tsv, each
# one's sha256), the capture script, or the content of a file the side reads
# (<side>.inputs). The Steam session is not tracked.
# docs/dev/game-runtime.kb/cvarlist-capture.md
# redo runs this with cwd = data/cvarlist/; the repo root is two up.
set -euo pipefail

redo-ifchange ../../bin/cvarlist-capture ../dlls/file.tsv "$2.inputs"
tmp=$(mktemp -d "$2.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
../../bin/cvarlist-capture "$2" "$tmp" >&2
mv "$tmp/"*"-$2.log" "$3"
