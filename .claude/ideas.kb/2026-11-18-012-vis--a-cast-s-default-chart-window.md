---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: a cast's default chart window

## The Idea

AWAITS THE USER'S RULING against their "default 2 periods". A cast's chart defaults to 2 cooldown periods (about 60 s), which crushes the damage: Leech's 5 s takes 8% of the width, and a 0.1-0.7 s cast delay is 1-10 px wide. The user's "width as wind-up" shows in no default view.

Smallest fix: for a cast, default the horizon to the first cast's last land plus about 20% (6 s for Leech), and keep `x period` for anyone who wants the cycle. Separately the user should judge whether a nonzero default gun distance (e.g. 20 m) is worth giving up an exact in-game check (at the defaults, guns and melee have zero width).

The horizon logic is in `apps/vis/server/src/vis_server/queries.py`.

## Exploration Notes

Provenance (the handoff files are removed): Finding 1 and Open Questions of `.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md` at `17ebf82` (`git show 17ebf82:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
