---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md
  - ../../../apps/vis/server/src/vis_server/timeline.py
  - ../../../apps/vis/server/src/vis_server/timeline_test.py
  - ~/.claude/skills/mutation-testing
---

# `timeline_test.py`: observe each assertion fail, and make basedpyright clean

**Parent:** <https:../2026-11-18-000-vis-app.md> (wave 1)

## Problem Statement

`timeline.py` and its 10 tests pass, but no assertion has been seen to fail,
and `uv run basedpyright` reports 3 errors (one is `Any | float` passed as
`int`, which is probably the `Gun(**{**vars(PAIGE), …})` in the test).

Mutation-test `timeline.py` (Skill(mutation-testing)), one mutant at a time,
and restore the module after each. The coordinator's planned mutants:
- drop the single-shot intra branch;
- `(burst-1)*intra`;
- drop pellets;
- drop reload;
- drop travel;
- swap the horizon checks;
- drop `cycle=n`;
- `return` → `n += 1` in the no-period branch, which loops forever, so run it
  under a timeout.

For each survivor, harden or add a test. Fix the type errors without weakening
"all". A previous attempt ran every mutant from one unreviewed Bash loop, and
the user stopped it. Run them in small, readable steps.

Behavior of `timeline.py` does not change. If a mutant shows a real bug, fix it
and say so.

**Scope (only these files):** `apps/vis/server/src/vis_server/timeline.py`,
`apps/vis/server/src/vis_server/timeline_test.py`

## Steps

Each mutant: injected in `timeline.py`, tests run with `python -B` after removing
its `.pyc`, under `timeout 20`, then the module restored from
`trash/timeline-mutants/`. "→" names the test(s) that kill it.

- [x] fix the 3 basedpyright errors: `Gun(**{**vars(PAIGE), …})` → `replace(PAIGE, travel=0.25)`
- [x] M1 single-shot intra branch dropped → 4 `DescribeGunCycle` tests
- [x] M2 period `(burst-1)*intra` → `it_spaces_a_burst…`, `it_reproduces_the_ui_dps`
- [x] M3 pellets dropped → `it_sums_pellets…`, `it_reproduces_the_ui_dps`
- [x] M4 reload dropped from period → `it_reloads_after_the_clip`, `…ui_dps`
- [x] M5 travel dropped → `it_lands_after_the_travel_time`
- [x] M6a inner horizon check reads `land`: **survived**; added
  `it_keeps_a_hit_triggered_within_the_horizon_that_lands_past_it`, now killed
- [x] M6b outer `start > horizon` check dropped → hangs (timeout 124)
- [x] M7 `cycle=n` dropped → `it_numbers_repeats_in_the_cycle_field`
- [x] M8 no-period `return` → `n += 1`: killed only by hanging; bounded
  `it_fires_once_without_a_period` with `islice`, so it now fails fast
- [x] M9 `firing` without `/ burst` → `it_reproduces_the_ui_dps`
- [x] M10 `Cycle.reload` not passed → `it_reloads_after_the_clip`, `…ui_dps`
- [x] M11 label `shot {shot}`: **survived**; the travel test now compares the
  whole `Hit` (its values are exact floats), now killed
- [x] M12 hit-loop `break` → `continue`: survived, **equivalent** (see Decisions)
- [x] M13 `>` → `>=` on either horizon check → `it_numbers_repeats…`
- [x] final pytest + basedpyright, commit

## Decisions

- The mutation record lives here, not in `docs/dev/mutation-testing.kb/` as
  the skill suggests, because the brief limits scope to the two module files.
- I read "swap the horizon checks" as M6a (the inner check reads `land`) plus
  M6b (outer check dropped). I also ran each check with `>=` as M13.
- M12 is equivalent: `Cycle.hits` is documented as sorted by trigger, so once
  one hit is past the horizon, every later hit is too.

## Open Questions

- Nothing enforces that `Cycle.hits` is sorted. A source that emits hits out of
  order would silently lose hits in `repeat`. An assert in `Cycle.__post_init__`
  would make it fail loudly, but that changes behavior, which this brief rules
  out.
- `firing = shots * period / burst` assumes `shots % burst == 0`. With a
  partial last burst it charges a fractional burst. I didn't check whether any
  live gun has one; that belongs to `guns.py`.
- The `period > 0` assert in `repeat` is untested. Without it, `period=0` loops
  forever.

## Final report

- `timeline.py` is unchanged; no mutant exposed a bug.
- 14 mutants: 11 killed by the existing tests, M6a and M11 killed after
  hardening, and M12 equivalent. M8 used to be caught only by a hang; it now
  fails fast.
- Checks: `uv run pytest src/vis_server/timeline{,_test}.py` gives 11 passed,
  and basedpyright on both files gives 0 errors. The full suite currently has
  34 failures, all in the siblings' in-flight `casts_test.py` and
  `guns_test.py`.
- Changes: `apps/vis/server/src/vis_server/timeline_test.py`.
