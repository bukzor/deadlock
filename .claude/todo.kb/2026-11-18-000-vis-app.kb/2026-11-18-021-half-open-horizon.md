---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md   # "Model": the window is [0, horizon)
  - ../../../apps/vis/server/src/vis_server/timeline.py
  - ../../../apps/vis/server/src/vis_server/measures.py
---

# The horizon is half-open: N periods hold exactly N cycles

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 2)

## Problem Statement

Both `repeat` and `landed_by` in `timeline.py` include the horizon itself. A
default horizon of 2 periods therefore counts a third cycle's first hit when it
lands exactly at the horizon. For example, `vis-server query timeline
hero=hero_atlas ability=melee_heavy` gives "Damage in the first 2 s" as three
swings, and "DPS over the first 2 s" as 1.5 × the steady DPS. The user asked
for the default to show "two full cycles", so a window of N periods must hold
exactly N cycles. Then the average DPS over it equals the steady DPS.

**Decided:** the window is `[0, horizon)`. A hit is unrolled when its trigger is
before the horizon, and counted and sent when it lands before the horizon. The
design doc already says this, under "Model".

**Check:** with the default horizon, `average_dps` equals `steady_dps`
for a gun, a melee swing and a repeating cast. Test that across every live
hero's gun and melee, the way `ability_profiles` is checked. Drive each new
assertion to red with the old `<=`.

**Scope:** `apps/vis/server/src/vis_server/timeline.py`, `measures.py` (only if
it compares against the horizon), and their tests. Also any other `*_test.py`
whose expectations move because of this change, and only those.

## Steps

- [x] Tests first: timeline (trigger and land at the horizon, N periods hold N cycles), measures (land at the horizon, average equals steady), real-data sweep of every live hero's gun and melee at 2 periods.
- [x] Red with the old `<=`/`>`: all 6 new or moved assertions failed; green after the change.
- [x] `timeline.py`: `repeat` stops at `>= horizon`, `landed_by` keeps `land < horizon`; docstrings in `timeline.py` and `measures.py` say `[0, horizon)`.

## Decisions

- The real-data sweep lives in `measures_test.py` (`DescribeDefaultHorizon`), since `average_dps` is a measure; guns at distance 0, melee at windup 0.25.
- Casts are covered by the synthetic cases only (no live-hero sweep); the repeating-cast path is the same `repeat`.
- `queries_test.py` expectations moved (default now gives 2 hits, not 3; a hit landing exactly at horizon 1 is out), so I edited them.

## Final report

`uv run pytest` and `basedpyright` clean. Code: `timeline.py`; `measures.py` docstring only (it compares nothing itself). Tests: `timeline_test.py`, `measures_test.py`, `queries_test.py`.
