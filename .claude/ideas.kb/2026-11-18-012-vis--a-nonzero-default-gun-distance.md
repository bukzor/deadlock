---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: a nonzero default gun distance

## The Idea

At the defaults (distance 0, wind-up 0), gun and melee bars have zero width, so
the user's "width as wind-up" shows only once a distance or wind-up is typed. A
nonzero default gun distance (e.g. 20 m) would show bullet travel, at the cost
of the default numbers no longer matching a point-blank in-game check. The
agent recommends keeping 0. Awaits the user.

The default is in `apps/vis/server/src/vis_server/queries.py`.

The cast half of this entry is settled: the user ruled "yes, two cycles"
(`HORIZON_DEFAULT` in `apps/vis/docs/dev/claims.kb/horizon-default.md`).

## Exploration Notes

Provenance (the handoff files are removed): Finding 1 and Open Questions of `.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md` at `17ebf82` (`git show 17ebf82:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
