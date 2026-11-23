---
managed-by: Skill(llm-subtask)
status: done
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

- [x] lookup: `Item` reads its properties (TDD)
- [x] lookup: `Ability.bonus(tier, prop)` reads an upgrade tier (TDD)
- [x] `git mv` the model into measurements; constants through the lookup
- [x] stdout `cmp` model.before.txt; all checks; commit

## Decisions

- **Path: `bukzor_deadlock_measurements/crimson_slash_model.py`**, beside
  `check` and `summary`, as briefed. The basename is kept, so the rename
  pairs as a pure move plus edits, and the name still says which experiment
  it models. A `models/` subpackage mirroring `experiments/` was rejected:
  one module doesn't earn a package.
- **Lookup addition: `Item` subclasses `Ability`.** An item is an
  `abilities.vdata` entity, so it now carries its `tree` and every `Ability`
  reader (`value`, `scale`, ...). `Lookup` builds it with the tree (new
  `_tree` helper, shared with `ability`). Tested in `lookup_test`.
- **Lookup addition: `Ability.bonus(tier, prop) -> Bonus(amount, kind,
  stat)`**, reading `m_vecAbilityUpgrades`. `kind` is `m_eUpgradeType`
  (absent means `EAddToBase`; the data also has `EAddToScale`, `EMultiply*`).
  `bukzor_deadlock.ability_upgrades` was not reused: it keeps bonuses as
  verbatim strings and drops the kind. Tested in `entities_test`.
- **Readability layer:** the `@final` namespaces stay, and each constant is
  one lookup read, using three small helpers (`percent`, `scale_factor`,
  `spirit_scale_bonus`). The prediction code is unchanged. The constants
  are read at import, from English names (`"Crimson Slash"`, `"Tankbuster"`,
  `"Mystic Reverb"`); the key comments stay.

## Open Questions

- Frozen unit 008 still names `./bin/shell python crimson_slash_model.py`.
  It is a record, so it stays as written.

## Final report

**Checks:** model stdout `cmp` equals `trash/package-split/model.before.txt`.
All 12 read constants `==` the old hardcoded ones (build 6864), so there is
no finding. Root pytest and pyright pass, and so do vis pytest and
basedpyright; `golden.after.txt` `cmp` equals `golden.before.txt`. No
deviations from the brief.

Run: `./bin/shell python -m bukzor_deadlock_measurements.crimson_slash_model`.

Constant block, before -> after (one line each):

| constant | before | after |
|---|---|---|
| `CrimsonSlash.Damage.BASE` | `55` | `SLASH.value("Damage")` |
| `.Damage.SPIRIT_SCALE` | `0.37` | `scale_factor(SLASH, "Damage")` |
| `.Damage.SPIRIT_SCALE_T3` | `0.6` | `spirit_scale_bonus(SLASH, 3, "Damage")` |
| `.Heal.BASE` | `55` | `SLASH.value("HealFixedHealth")` |
| `.Heal.SPIRIT_SCALE` | `1.035871` | `scale_factor(SLASH, "HealFixedHealth")` |
| `.Heal.SPIRIT_SCALE_T3` | `0.4` | `spirit_scale_bonus(SLASH, 3, "HealFixedHealth")` |
| `.Heal.MAX_HEALTH_T2` | `0.06` | `SLASH.bonus(2, "HealMaxHealth").amount / 100` |
| `Tankbuster.DAMAGE` | `40` | `TANKBUSTER.value("Damage")` |
| `.CURRENT_HEALTH_DAMAGE` | `0.075` | `percent(TANKBUSTER, "CurrentHealthDamage")` |
| `MysticReverb.ECHO_DAMAGE` | `0.5` | `percent(REVERB, "TechDamagePercent")` |
| `.IMBUE_LIFESTEAL` | `0.22` | `percent(REVERB, "ImbueAbilityLifesteal")` |
| `.HERO_LIFESTEAL` | `0.08` | `percent(REVERB, "AbilityLifestealPercentHero")` |

where `SLASH`, `TANKBUSTER`, `REVERB` = `GAME.ability("Crimson Slash")`,
`GAME.item("Tankbuster")`, `GAME.item("Mystic Reverb")`, and `GAME = load()`.
