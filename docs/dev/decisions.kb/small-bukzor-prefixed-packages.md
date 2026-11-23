---
status: accepted
date: "2026-11-23"
---

# Small packages, `bukzor`-prefixed, named as if bound for PyPI

> [!@bukzor] ruled 2026-11-23, recorded sensatim -- prefer small packages
> over too-large ones: a unit that *can* move cleanly into another package
> is significant enough to be held separate.

> [!@bukzor] ruled 2026-11-23, recorded sensatim -- a `bukzor` prefix marks
> packages by the owner, for the owner. An unprefixed name is reserved for
> packages so simple, and so stable, that the owner is happy to accept
> patches.

Nothing here is published. Every package is still named as if it might be,
distribution and import name alike (`bukzor-redotools` / `bukzor_redotools`),
because a rename now is one mechanical commit and a rename later touches
every import. None qualifies for the unprefixed tier: game patches churn the
internal keys, and the DLL scanner rests on reverse-engineering heuristics.

## Layout

A package's directory is its distribution name.

| package | holds | depends on |
|---|---|---|
| `bukzor-deadlock` (repo root) | extraction, the `data/` views, `paths`, `loc` | `bukzor-dllscan`, `vpk`, `keyvalues3`, ... |
| `packages/bukzor-deadlock-lookup` | typed lookup of heroes, abilities and items by key or English name | `bukzor-deadlock` |
| `packages/bukzor-deadlock-damage` | one attacker's damage over time: cycles, hits, DPS, time to kill | lookup |
| `packages/bukzor-deadlock-evaluator` | build evaluation | damage, lookup, measurements |
| `packages/bukzor-dllscan` | the DLL scanner (`own-the-dll-scanner.md`) | stdlib only |
| `packages/bukzor-deadlock-measurements` | hand-recorded live sandbox readings (YAML), apart from the code that types and checks them | lookup |
| `apps/vis/server` (`vis-server`) | the JSONL protocol only | damage, lookup |

Apps are never published, so they keep plain names.

## Why each cut

- **Lookup apart from extraction:** extraction writes `data/` and needs the
  container and KV3 parsers; lookup only reads `data/` and the install's
  localization.
- **Damage apart from vis and the evaluator:** both consume it, and it moves
  out of vis with only import changes. In the root workspace (Python 3.12+)
  it is importable from vis's 3.14 workspace; the reverse edge was the
  blocker.
- **Measurements apart from the evaluator:** the owner's suggestion. Their
  activity differs: readings are hand-recorded in the live game and edited
  as data, while the evaluator is code that is judged against them. The
  package name is the agent's ([!DRAFT], vetoable): it matches the
  evaluator's "measure" loop.
- **DLL scanner apart from extraction:** a different runtime (a stdlib-only
  Windows-host Python), and only incidentally about Deadlock.

## What would change this

A package whose consumers always change in lockstep with another's, release
after release, is one package split in two: merge them.
