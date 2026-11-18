---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: casts that draw no hits at spirit 0

## The Idea

14 casts list as `kind: "cast"` but draw no hits at default settings (e.g. `ability_afterburn`, spirit 0). The player sees an empty chart with no reason. Evidence: `apps/vis/server/src/vis_server/casts.py` module docstring ("14 cycles have no hits at spirit 0").

Smallest fix: add a note to such a cycle saying its damage scales from spirit and is 0 at spirit 0, or mark the ability in `abilities`.

## Exploration Notes

Provenance (the handoff files are removed): `.claude/todo.kb/2026-11-18-000-vis-app.md` "Later" list at `53e22d0` (from unit 012 (`2026-11-18-012-end-to-end.md`)).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
