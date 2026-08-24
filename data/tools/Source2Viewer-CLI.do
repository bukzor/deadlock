#!/bin/bash
# The Source2Viewer-CLI binary at its natural path: a symlink into the
# provisioned payload directory.
#
# Why the indirection: the release ships the CLI plus four .so libraries that
# must sit beside it, so the unit redo can build is the whole directory
# (Source2Viewer-CLI.d — see that .do). But every consumer wants the binary,
# not the directory. This target lets them `redo-ifchange` the binary path and
# get the directory provisioned transitively, and keeps `.d` out of runtime
# paths (deadlock.s2v.binary_path, DEADLOCK_S2V).
#
# The link is relative, and $3 is a sibling of $1, so it stays valid after redo
# moves it into place. The CLI finds its libraries through the symlink.
# redo runs this with cwd = data/tools/.
set -euo pipefail

redo-ifchange Source2Viewer-CLI.d

ln -s Source2Viewer-CLI.d/Source2Viewer-CLI "$3"
