#!/bin/bash
# The engine's own `cvarlist` for one side, server or client: a launch of the
# installed game (bin/cvarlist-capture), on demand only (dlls.check/cvarlist.do).
# Gitignored: Valve data, and the client's values are the user's.
# redo-always: a capture reads what no tracked input records (the install, the
# Steam session, the user's archived settings), so it is never up to date; each
# run of the check launches the game afresh, once per side.
# docs/dev/game-runtime.kb/cvarlist-capture.md
# redo runs this with cwd = data/cvarlist/; the repo root is two up.
set -euo pipefail

redo-always
tmp=$(mktemp -d "$2.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
../../bin/cvarlist-capture "$2" "$tmp" >&2
mv "$tmp/"*"-$2.log" "$3"
