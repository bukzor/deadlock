---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: misplaced and vestigial pieces

## The Idea

`Gun`/`gun_cycle` live in `packages/bukzor-deadlock-damage/src/bukzor_deadlock_damage/timeline.py` but only `guns.py` uses them; `protocol.MeasureLine.label?` (`client/src/protocol.ts:59`) is optional "for older servers" that cannot exist (same repo, same process); `docs/dev/decisions.kb/vis-app.md` is still `status: proposed` (needs the user's review).

Smallest fix: move `Gun` into `guns.py`; make `label` required; flip the status once the user rules.

## Exploration Notes

Provenance (the handoff files are removed): Risk 5 of `.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-028-maintainability-review.md` at `2b797f3` (`git show 2b797f3:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-028-maintainability-review.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
