---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: player-facing wording lives in the modelling modules

## The Idea

Labels, checks and notes shown to players are strings inside `guns.py`, `melee.py`, `casts.py` and `measures.py` (e.g. the `Words` fields in `measures.py` ~line 40), mixed with the modelling. Changing wording means editing model code.

Smallest fix: move the strings into one module (`words.py`) the modelling modules import.

## Exploration Notes

Provenance (the handoff files are removed): As above: found by the plan's coordinator; no handoff-file source (`git show 53e22d0:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-029-future-improvements.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
