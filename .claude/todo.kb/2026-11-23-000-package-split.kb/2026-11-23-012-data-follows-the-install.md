---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - docs/dev/environment.kb/toolchain.md
  - all.do
---

# `data/` follows the installed game and the latest VRF

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 6, alone)

## Problem Statement

The data tracks the install and the latest VRF release; that's the
project's intent (`all.do` follows latest). During the package split, units
restored three files that a full `redo` rewrote, so the split's commits
would hold no patch drift: `data/deadlock-version.json`,
`data/tools/vrf-release.json` and `data/dlls/file.tsv`. At that point the
install was build 6864 (committed: 6860) and VRF 21.1 (committed: 20.1).

Run the full build (`redo` from the repo root) and commit everything it
changes as one commit of its own. Its message says what moved: the build
and VRF versions, then which committed views changed and how, summarized
from `git diff --stat` and a read of the TSV diffs (new or removed rows,
changed columns). If VRF 21.1 breaks extraction, stop and report the error.
Don't pin it back: the owner decides that.

This kb's `CLAUDE.md` tells other units to restore those three files. That
instruction is the coordinator's to retire after you land; leave it alone.

**Scope (only these files):** everything under `data/` that `redo`
rewrites and git tracks, and this file

## Steps

- [x] full `redo` (1m50s, no errors; log in trash/unit-012/redo.log)
- [x] read the diffs; commit the three changed files

## Decisions

## Open Questions

## Final report

VRF 21.1 extracted without error. Build 6860 -> 6864, VRF 20.1 -> 21.1. Only three tracked files changed: `deadlock-version.json`, `tools/vrf-release.json`, and `dlls/file.tsv` (same rows, new size/sha256 for the rebuilt DLLs). No gamedata.tsv, convars.tsv or concommands.tsv change: the patch moved no stats or convars. Committed as one commit.
