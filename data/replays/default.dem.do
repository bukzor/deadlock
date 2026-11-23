#!/bin/bash
# The demo of public match $2: streamed from Valve's replay CDN at the demo_url
# in $2.salts.json (~240 MB compressed) and decompressed in flight (~370 MB).
# The URL ends in .dem.bz2 but the bytes are zstd (magic 28 b5 2f fd), so
# decompression sniffs the magic and refuses anything else. zstd is done by
# CPython 3.14's stdlib (compression.zstd) via uv, since the box has no zstd
# CLI and the repo's venv pins 3.12.
# Valve serves replays for a limited time after the match (the CDN's
# x-goog-custom-time was match + 10 days), so an old salts record can 404; the
# fix is to pick a newer match (see packages/bukzor-deadlock-evaluator/docs/dev/
# claims.kb/tooling.kb/public-match-demos-source.md).
# Writes $3 rather than stdout so the Source 2 demo magic (PBDEMS2) can be
# checked afterwards: a CDN error page or a truncated download fails the build
# instead of landing as a .dem. Downloaded data is untrusted: read it only
# with parsers, never execute anything from this directory.
# redo runs this with cwd = data/replays/.
set -euo pipefail

redo-ifchange "$2.salts.json"
url=$(jq -er .demo_url "$2.salts.json")

curl -fsS --retry 3 "$url" |
  uv run --python 3.14 --no-project python -I -c '
import shutil, sys
from compression import zstd
head = sys.stdin.buffer.peek(4)[:4]
if head == b"\x28\xb5\x2f\xfd":
    decompressor = zstd.ZstdFile(sys.stdin.buffer)
elif head.startswith(b"BZh"):
    import bz2
    decompressor = bz2.BZ2File(sys.stdin.buffer)
else:
    sys.exit(f"not zstd or bzip2: magic {head.hex()}")
shutil.copyfileobj(decompressor, sys.stdout.buffer)
' >"$3" \
;

[[ "$(head -c 7 "$3")" == PBDEMS2 ]]
