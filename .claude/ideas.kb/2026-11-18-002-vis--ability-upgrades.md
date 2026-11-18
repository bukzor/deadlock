---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: ability upgrades

## The Idea

Ability upgrades (`data/gamedata.tsv/ability_upgrades.tsv`) are not modeled; only raw upgrade notes appear. Evidence: `docs/dev/decisions.kb/vis-app.md` ("Charges, upgrades and level scaling are not modeled").

Smallest fix: unknown; start by reading `ability_upgrades.tsv` and listing which upgrades change damage, cooldown or duration.

## Exploration Notes

Provenance (the handoff files are removed): `.claude/todo.kb/2026-11-18-000-vis-app.md` "Later" list at `53e22d0`.

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
