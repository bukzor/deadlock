---
managed-by: Skill(llm-subtask)
status: open
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
