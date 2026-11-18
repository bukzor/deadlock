#!/bin/bash
# Provision boon (github.com/pnxenopoulos/boon), the Deadlock demo parser the
# evaluator's `observe` wraps: a Rust core with Python bindings and a `boon`
# CLI, published on PyPI as boon-deadlock. The pin is the version below; bump
# it here and redo rebuilds.
# A directory target (reference.kb/redo-do-scripts.md): the payload is a whole
# venv, built relocatable so its entrypoints survive redo's $3 -> $1 move.
# PyPI ships only manylinux wheels and this host is musl, so uv builds the Rust
# core from the sdist with the rustup toolchain (minutes, once; uv caches the
# built wheel). Python is the repo's pin so the evaluator's own venv can later
# reuse that cached wheel.
# redo runs this with cwd = data/tools/.
set -euo pipefail

boon_version=0.19.0

redo-ifchange ../../.python-version

# progress/summaries belong on stderr; a directory target writes no stdout
exec >&2

uv venv --relocatable --python "$(cat ../../.python-version)" "$3.tmp"
uv pip install --python "$3.tmp/bin/python" "boon-deadlock==$boon_version"

# smoke-test the entrypoint: needs no demo, exercises the compiled core
"$3.tmp/bin/boon" datasets >/dev/null

# pre-clear the stale directory so redo's file-oriented $3 -> $1 move doesn't
# nest, keeping the prior good build until the new one is installed
if [ -e "$1" ]; then
  mv "$1" "$1.old"
fi
mv "$3.tmp" "$3"
if [ -e "$1.old" ]; then
  rm -r "$1.old"   # no -f: surface unexpected state loudly
fi
