---
managed-by: Skill(llm-subtask)
status: open
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

## Decisions

## Open Questions

## Final report
