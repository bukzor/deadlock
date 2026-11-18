---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: measure the melee wind-up in-game

## The Idea

Melee wind-up (the bar width) is a guess, not a measurement; the default is 0. Evidence: `apps/vis/server/src/vis_server/melee.py`.

Smallest fix: time a swing in-game and put the number (with its source) into `melee.py`.

## Exploration Notes

Provenance (the handoff files are removed): `.claude/todo.kb/2026-11-18-000-vis-app.md` "Later" list at `53e22d0`.

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
