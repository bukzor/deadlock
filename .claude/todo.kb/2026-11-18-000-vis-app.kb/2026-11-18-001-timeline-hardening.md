---
managed-by: Skill(llm-subtask)
status: open
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

## Decisions

## Open Questions

## Final report
