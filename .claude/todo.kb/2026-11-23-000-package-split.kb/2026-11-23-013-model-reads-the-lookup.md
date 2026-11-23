---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-012-data-follows-the-install.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - crimson_slash_model.py
  - packages/bukzor-deadlock-measurements/
  - packages/bukzor-deadlock-lookup/src/
  - 2026-11-23-004-lookup-api.md (its Decisions only)
  - 2026-11-23-005-adopt-lookup.md (its Decisions only)
---

# The owner's Crimson Slash model reads its constants through the lookup

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 7, alone)

## Problem Statement

`crimson_slash_model.py` at the repo root is the owner's model of one
Crimson Slash cast. It predicts damage and self-heal and prints them beside
the readings in `bukzor_deadlock_measurements.experiments.crimson_slash`. Its
game constants are hardcoded in readable namespaces (`CrimsonSlash.Heal.BASE
= 55  # HealFixedHealth`, `Tankbuster.CURRENT_HEALTH_DAMAGE`,
`MysticReverb.IMBUE_LIFESTEAL`, the T2/T3 upgrade values). The owner wants
those constants read from the game data through the lookup, as near as
possible to the current readability.

- **Move it into the measurements package** as a program over its data: a
  module beside `check` and `summary`, runnable with `python -m`. The owner
  agreed it belongs there. Choose the module path and record why. `git mv` it
  so the rename pairs.
- **Read the constants through the lookup:** the ability, the two items, and
  the upgrade tiers. If the lookup lacks a reader the model needs (upgrade
  tiers, or an item's properties), add it in
  `packages/bukzor-deadlock-lookup/` with its test. Record each addition in
  Decisions.
- **Keep it readable.** If the raw lookup calls read worse than the
  namespaces, add a thin layer that gives the model its named constants (for
  example, frozen dataclasses built from the lookup) and keep the
  prediction code reading as it does now. The owner judges readability: show
  the before/after of the constant block in your Final report.
- **The output must not change:** stdout must equal
  `trash/package-split/model.before.txt` byte for byte. If a constant read
  from the data differs from the hardcoded one (unit 012 may have moved the
  data to a newer build), that's a finding. Report the constant, both values
  and the output's diff. Don't fudge the read to match.
- **Docstring:** make it say where the constants come from now, and how to
  run the model.

**Scope (only these files):** `crimson_slash_model.py` (moved),
`packages/bukzor-deadlock-measurements/src/`,
`packages/bukzor-deadlock-lookup/src/`, and this file

## Steps

## Decisions

## Open Questions

## Final report
