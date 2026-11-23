---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-004-lookup-api.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - crimson_slash_test_data.py
  - packages/bukzor-deadlock-lookup/
  - packages/bukzor-deadlock-evaluator/docs/dev/claims.kb/architecture.kb/measure-is-the-ground-truth-loop.md
  - packages/bukzor-deadlock-evaluator/docs/dev/CLAUDE.md
  - 2026-11-23-004-lookup-api.md (its Decisions and Open Questions only)
---

# Crimson Slash readings become the evaluator's first calibration data

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 4, beside unit 005)

## Problem Statement

`crimson_slash_test_data.py` at the repo root holds live sandbox readings:
the owner's measurements, which the "measure" evaluator is judged by. Move
it into `packages/bukzor-deadlock-evaluator/src/bukzor_deadlock_evaluator/`,
in a module path that names its role as measured ground truth. Choose the
path and record why.

What changes and what doesn't:

- **Readings are observations, not lookups.** Never replace a recorded
  number with a value from the data. The sandbox dummy's 10686 health
  differs from the data's `hero_targetdummy` (2990): the sandbox
  configures its dummies.
- **Item names are checked against the lookup.** Each item list names
  real items. Assert the equal-cost swaps the comments now only claim: the
  Tankbuster scenarios replace Rapid Recharge, and the Reverb scenarios
  replace Refresher or Focus Lens (unconfirmed which). Keep the record
  readable for hand editing: the owner adds scenarios by hand.
- **The comment on regen is unsourced.** "Repeated measurements disagreed;
  these are the values that each recurred" appears nowhere in the owner's
  original notes. Keep the comment, and list it in Open Questions for the
  owner.
- **Tests:** add one beside the module that checks the item lists and
  swaps against the real data. Keep `python -m <module>` printing the
  summary table.

Record the module's existence in the evaluator ledger, as that ledger's
`CLAUDE.md` says to.

**Scope (only these files):** `crimson_slash_test_data.py` (moved),
`packages/bukzor-deadlock-evaluator/src/` (the new module and its test), the
evaluator's `docs/dev/claims.kb/` entry for it, and this file

## Steps

## Decisions

## Open Questions

## Final report
