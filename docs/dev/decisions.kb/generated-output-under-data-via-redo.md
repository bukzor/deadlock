---
status: accepted
date: "2026-06-15"
---

# Generated output under data/, regenerated with redo

All derived artifacts — VPK manifests, extracted/raw files, decompiled assets,
parsed KV3 — live under `data/` and are produced by `redo` `.do` scripts. Most of
`data/` is gitignored; the curated TSV views (`data/gamedata.tsv/`) are the
exception and ARE committed (see `commit-diffable-data-let-git-diff.md`).
Vendored external tools (the VRF CLI) live under `data/tools/`, each its own
redo directory target — provisioning is a dependency, not a documented chore.

## Why

- The source of truth is the game install, not the repo. Outputs are large and
  reproducible, so they don't belong in git.
- `redo` makes regeneration *correct*: a target `redo-ifchange`s both the source
  VPK and the pinned tool binary, so an engine/patch bump or tool upgrade
  invalidates exactly the stale outputs. This is what makes patch-diffing
  deterministic and repeatable.

## Conventions

- Python does the parsing; `.do` scripts orchestrate (declare deps, run
  `python -m ...`, place files). Keep `.do` scripts small.
- Never commit raw or bulk data under `data/` — only the transformative TSV
  views (and their `.do` sources) are tracked.

## What would change this

If an artifact becomes a stable, reviewable input (e.g. a curated schema), it can
graduate out of `data/` into version control — but raw/derived game data stays
generated.
