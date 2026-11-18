---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md
  - ../../../apps/vis/server/src/vis_server/timeline.py
  - ../../../apps/vis/server/src/vis_server/casts.py
  - ./2026-11-18-005-casts.md   # its Decisions and Open Questions
---

# `casts.py` ticks trigger at the cast; `Cycle` enforces sorted hits

**Parent:** <https:../2026-11-18-000-vis-app.md> (wave 2)

## Problem Statement

Two corrections to wave 1. Both come from the design's "Model" section,
which now states them.

1. **Ticks trigger at the cast.** `casts.py` currently sets a damage-over-time
   tick's trigger to the start of its interval. The design now says a tick's
   trigger is the cast, so the bar spans from the cast to the tick's land.
   The user defined the left edge as the triggering event, and `trigger` must
   mean the same thing for every source. Update `casts.py`, its tests, and any
   docstring that describes the old convention.
2. **`Cycle` enforces sorted hits.** `repeat` silently drops hits when
   `Cycle.hits` isn't sorted by trigger (unit 001). Make `Cycle` assert this
   when it is constructed, with the assert showing the offending values, and
   test that.
   - After the change, all of `apps/vis/server` must still pass: the hits
     from guns, melee and casts must all be sorted.
   - If a source in another unit's files breaks the assert, report it; don't
     fix it there.

**Scope (only these files):** `apps/vis/server/src/vis_server/{casts,casts_test,timeline,timeline_test}.py`

## Steps

- [x] Ticks trigger at the cast: red test, `casts.py`, docstrings
- [x] `Cycle` asserts sorted hits: red test, `timeline.py`
- [x] Whole server suite and basedpyright clean
- [x] Commit

## Decisions

- `Cycle.__post_init__` asserts on the offending adjacent pairs, not the whole
  list, so the message shows exactly which hits are out of order. Equal
  triggers are allowed: every cast hit now triggers at 0.
- `casts.cycle` no longer sorts its hits, and `it_orders_hits_by_trigger` is
  gone. All of its triggers are 0, so the sort did nothing, and `Cycle` now
  enforces the order for every source.

## Open Questions

None.

## Final report

- Checks: `uv run pytest` 81 passed, 0 skipped (this includes the roster-wide
  real-data tests for guns, melee and casts, so no source's hits break the
  assert); `uv run basedpyright` 0 errors on the whole server.
- Red observed for both new `DescribeCycle` tests: with the assert removed
  (`DID NOT RAISE`), and with `>` mutated to `>=` (rejects shared triggers).
- No deviations from the brief. Results are in `casts.py` (tick trigger,
  docstrings), `timeline.py` (`Cycle.__post_init__`) and their tests.
