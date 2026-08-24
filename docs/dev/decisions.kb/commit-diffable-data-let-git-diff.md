---
status: accepted
date: "2026-08-24"
supersedes: "2026-06-15 (committed the raw flats + manifest instead)"
---

# Commit line-grained data; let git diff do the diffing

Rather than maintaining bespoke diff code, deterministic outputs are committed
to git as line-grained text. To understand a patch: regenerate against the new
install and read `git diff`.

## What gets committed: the transformative views only

The committed artifacts are the curated TSV views (`data/gamedata.tsv/*.tsv`)
plus `data/deadlock-version.json`, a build-provenance stamp from the install's
`steam.inf`.

The raw intermediates — the flattened per-file JSONL (`data/gamedata.flat/`)
and the VPK manifest — are **local build outputs, never committed**. They are
near-verbatim Valve game data; the TSVs are our transformative work (chosen
columns, joins, derived values). Publishing only the transformative layer is
the defensible posture for a public repo, and the TSVs are the consumable
artifact anyway. The pre-publication history was rewritten to remove the raw
files entirely.

**Accepted trade-off:** git diff now only shows patch changes in the curated
views. Broad changes (a stat no view covers, asset churn) are visible only
transiently in the local flats/manifest at rebuild time. The mitigation is to
grow view coverage: when a patch investigation needs data no view exposes,
that's the prompt to add or widen a view.

## Committing a redo target: adopt it, don't delete it

A committed build output is a file redo must own but git creates. redo decides
ownership from its own state database (djb's rule: never clobber a file you
didn't generate), which a fresh clone doesn't have — so it would treat the
committed views as hand-written and skip them *while exiting 0*, leaving stale
data with no error. Deleting them first, the obvious workaround, forfeits
incrementality and destroys the outputs when a build then fails.

Instead `all.do` runs `redo-adopt` (from `packages/bukzor-redotools/`, a
dev dependency kept separate so it can be published on its own), which makes
redo rebuild a committed output when it's out of date instead of skipping it.
Alternatives weighed: a second committed tree with a publish step and a
`check` target (more moving parts, and adopt makes the drift it guards against
impossible); making the whole directory one target, since redo exempts
directories from the ownership rule (loses per-view targets, and puts a `.d`
in a published path).

## Why git diff

- `git diff` is a better, free diff engine than anything we'd write — the data
  is deterministic and sorted, so regeneration produces minimal, localized
  line changes.
- It removed a whole module (the old `deadlock.diff`).

## Grain is the whole game

A diff is only useful if a single logical change maps to a single line. Each
committed output is shaped to that grain: one entity per row, columns for the
stats that matter, stable sort. When adding a view, decide its grain
deliberately: the goal is "one meaningful change ≈ one changed line".

(The same principle shaped the local flats — one leaf scalar per line, one
file per vdata source — because the redo pipeline still diffs them
implicitly: an unchanged flat short-circuits view rebuilds via `redo-stamp`.)

## What does NOT get committed

Everything else under `data/`: the raw flats and manifest (above), bulk/binary
assets (textures, models, audio), the vendored VRF tool, and intermediate
extraction dirs. See `generated-output-under-data-via-redo.md` for the
data/ + redo mechanics.
