---
status: accepted
date: "2026-11-09"
---

# A lossless per-DLL store, one atom per (facet, DLL)

Data about the game DLLs is a store, not a dump tuned to one question. A
**facet** is one side of a DLL that one producer reads: its file, its load,
its convar queue, its command queue. Each facet is dumped losslessly for every
DLL, as one JSON document, `data/dlls/<facet>/<dll>.json`, by one process with
its own redo target. The documents are the source. The committed TSVs and the
reading views are adapters over them, and so is any filter for a purpose (only
the server's cvars, only the DLLs that carry queues). Layout:
`../cvar-dump.kb/output-views.md`.

## Why

- **The next question finds the store still valid.** A filter baked into the
  dump (only the tier0 importers, only convars) would need a new scan for the
  next question. Kept outside, it becomes a fact read off the store: on 6860,
  every DLL that carries a queue is tier0 or loads it
  (`../cvar-dump.kb/dll-coverage.md`).
- **Lossless means every item, by a stated rule.** Each document holds all its
  source exposes. Bulk that is pure noise becomes a count and a hash. Values
  take the JSON type that fits the data. Adapting them to a TSV cell is a
  view's job.
- **Atomic production keeps rebuilds exact and parallel.** Each atom depends on
  its DLL and on the code that produces its facet. A patch re-runs only the
  DLLs it changed. A change to one WSL-side facet re-runs only that facet,
  though a change to the scanner re-runs every load-time atom. `redo -j` runs
  every atom at once. Process overhead is ~0.2 s per atom (6860,
  `../probes/load_time.py`). On 6860, a forced rebuild of the 91 `convars`
  atoms, with their aggregate and check, takes 22 s at `-j8`.
- **A process per DLL contains its failures.** A DLL that crashes fails only
  its own atom. A DLL that hangs fails on a timeout and is then excluded,
  since four tools DLLs hang in `LoadLibrary` and leave an unkillable process.

Only the aggregates (`data/dlls/<facet>.tsv`) are committed, per
`commit-diffable-data-let-git-diff.md`. The documents are near-verbatim Valve
data, so they stay local.

## Alternatives weighed

- **One scan process over all DLLs, writing one dump:** a crash or hang in any
  DLL loses them all, any code change re-runs them all, and it runs serially.
- **A purpose-tuned dump** (convars from the tier0 importers): smaller, but
  every new question needs a new scan, and "which DLLs matter" becomes an
  assumption nobody checks.
- **Committing the documents:** they repeat the aggregates in a less diffable
  shape, and they are Valve's data.

## What would change this

Facets that would share an expensive acquisition share an atom instead. One
case is open: `convars` and `concommands` scan the same writable sections
twice, and merge into one atom if that scan proves slow. If per-atom overhead
came to dominate the build, batching atoms per process would be the fix, with
the per-DLL documents kept.
