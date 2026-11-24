---
status: accepted
date: "2026-11-24"
---

# Explode VPKs to plain files, one redo target per pak directory

> [!DRAFT] agent-authored 2026-11-24 (vo-transcripts unit 001), vetoable.

Extractions that need raw game files (captions, soundevents, audio) start
from `data/vpk/`, a byte-for-byte copy of VPK contents on the Linux disk,
not from the VPKs. `data/vpk/default.d.do` holds the target grammar:

- `data/vpk/<pak>.d` -- a whole pak (`citadel`, `core`, `citadel_<lang>`).
- `data/vpk/<pak>/<dir>.d` -- one directory of it, e.g.
  `data/vpk/citadel/sounds/vo.d`. Its contents are that directory's: a VPK
  file `sounds/vo/a/b.vsnd_c` lands at `sounds/vo.d/a/b.vsnd_c`.
- `data/vpk/all` -- every pak whole.

Each pak keeps its own tree; nothing is merged, so overlay order stays the
consumer's call. No decompiling: that is each consumer's step downstream. A
target rebuilds when its pak's `pak01_dir.vpk` (every patch rewrites it) or
the explode code changes.

## Why

- **The subset is a directory, not a glob.** A target name has to carry
  the selection, and a directory path maps onto a file path one to one;
  glob syntax (`*`, `**`) in target names is hostile to the shell and to
  redo. Every consumer we know of wants whole directories
  (`soundevents/vo`, `sounds/vo`). A consumer wanting a sparser set filters
  the directory it depends on.
- **Whole-pak explode is opt-in.** Measured here (WSL, install on the
  Windows drive over 9P): `citadel/sounds/vo.d` -- 83,015 files,
  2.6 GiB -- takes 74 s; `core.d` (623 MiB) plus a locale pak plus
  `citadel/soundevents/vo.d` take 9 s. The whole `citadel` pak is 158,599
  files, 34.5 GB by its index; an interrupted run wrote 22.5 GB of it in
  about 7 min, so the whole pak takes about 11 min. Nothing needs all of
  it, and every patch would recopy it, so the repo's `redo all` does not
  depend on `data/vpk/all`.
- **Every explode checks for room first.** It sums its files' sizes from
  the index and refuses to start unless 20 GB would stay free under
  `paths.free_space_dir()`. On a WSL host the Linux disk is a virtual disk
  that grows on the Windows drive, and filling that drive crashes
  everything (`../environment.kb/host-alpine-musl-gcompat.md`), so there
  `localhost.env` points `DEADLOCK_FREE_SPACE_DIR` at the Windows drive.
- **Our own byte reader, the `vpk` library's index.** The library parses the
  directory tree (`bukzor_deadlock.archive.read_entries`), but its per-file
  reader reopens the data archive for every file; over 9P that ran ~9x
  slower (5-15 MiB/s) than one open per archive with reads in offset order
  (~47 MiB/s on small files). `bukzor_deadlock.explode` does the latter and
  checks every file's CRC32 against the index as it writes.

## Alternatives weighed

- **Each consumer opens the VPKs itself** (as `extract.py` does through VRF):
  every consumer re-pays the 9P cost and carries its own VPK plumbing.
- **A merged overlay tree** (`citadel` over `core` over locales): bakes one
  overlay order into the data, and hides which pak a file came from.
- **Incremental explode by CRC** (rewrite only changed files): would make a
  patch cheap, at the cost of state outside redo's model. Not needed while
  the subsets in use rebuild in about a minute.

## What would change this

A consumer needing a whole pak on every patch (makes incremental explode
worth it), or one whose selection is not a directory (add a selector to the
target grammar then, not before).
