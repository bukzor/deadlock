---
status: accepted
date: "2026-06-15"
---

# Commit line-grained data; let git diff do the diffing

Rather than maintaining bespoke diff code, the deterministic outputs are
committed to git as line-grained text. To understand a patch: regenerate the
outputs against the new install and read `git diff`.

## Why

- `git diff` is a better, free diff engine than anything we'd write — and the
  data is already deterministic and sorted, so a regeneration produces minimal,
  localized line changes.
- It removed a whole module (the old `deadlock.diff`): the manifest and the
  game-data JSONL are now self-diffing.

## Grain is the whole game

A diff is only useful if a single logical change maps to a single line. So each
output is shaped to the right grain:

- **manifest** (`data/manifest.jsonl`) — one file per line, path-sorted. A
  changed/added/removed file is one line.
- **game data** (`data/gamedata.flat/<file>.jsonl`, one per vdata) — flattened
  to one *leaf scalar* per line (`{path, value}`), sorted. A balance change to
  one stat is one line, in the file named for its source; a whole-record-per-line
  form made 27 KB lines that `git diff` couldn't resolve, and a single merged
  stream repeated the source filename on every line and rewrote one 28 MB git
  blob per patch. The reusable re-graining step is `deadlock.flatten`.

When adding a new output, decide its grain deliberately: if a likely single
change would rewrite a large line, flatten finer; if lines are so fine the file
is noise, coarsen. The goal is "one meaningful change ≈ one changed line".

## What does NOT get committed

Commit exactly what needs the game install to regenerate; build what derives
from the repo alone. The TSV views (`data/gamedata.tsv/`) derive entirely from
the committed flats, so they are gitignored build outputs — `redo` them on
demand. Committing them would also fight redo: git checkouts count as "modified
outside redo", which redo refuses to clobber. Bulk/binary assets (textures,
models, audio), the vendored VRF tool, and intermediate extraction dirs stay
gitignored too. See `generated-output-under-data-via-redo.md` for the
data/ + redo mechanics.
