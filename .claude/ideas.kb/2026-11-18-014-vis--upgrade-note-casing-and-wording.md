---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: upgrade note casing and wording

## The Idea

Upgrade notes mix casing: game labels are Title Case ("T2 Lifesteal 20"), fallbacks are lower-case ("T2 dps 0.6", "T3 beam split 0.93"), and the fallbacks read as raw property names to a player.

Smallest fix: one casing rule in the note builder in `packages/bukzor-deadlock-damage/src/bukzor_deadlock_damage/` (find it with `grep -rn "T2"`), and player words for the fallbacks.

## Exploration Notes

Provenance (the handoff files are removed): Open Questions of `.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-026-names-and-hp-zoom.md` at `85f36ff` (`git show 85f36ff:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-026-names-and-hp-zoom.md`); "round 1 #7" in `.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md` at `17ebf82` (`git show 17ebf82:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
