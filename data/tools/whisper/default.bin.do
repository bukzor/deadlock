#!/bin/bash
# A whisper.cpp GGML model, fetched from huggingface.co/ggerganov/whisper.cpp
# at a pinned revision and checked against its LFS sha256:
#   ggml-small.bin            the bulk ASR run (bukzor_deadlock.vo_asr)
#   ggml-large-v3-turbo.bin   escalation of doubtful clips, one at a time
# Add a model by adding its sha256 below. Local (gitignored): 0.5-1.6 GB each.
# redo runs this with cwd = data/tools/whisper/.
set -euo pipefail

revision=5359861c739e955e79d9a303bcbc70fb988958b1
case "$2" in
  ggml-small) sha256=1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b ;;
  ggml-large-v3-turbo) sha256=1fc70f774d38eb169993ac391eea357ef47c88757ef72ee5943879b7e8e2bc69 ;;
  *) echo "no pinned sha256 for $2.bin" >&2; exit 1 ;;
esac

# progress belongs on stderr; the model is written to $3
exec >&2

curl -fL --retry 3 -o "$3" "https://huggingface.co/ggerganov/whisper.cpp/resolve/$revision/$2.bin"
echo "$sha256  $3" | sha256sum -c -
