---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-001-rename.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - docs/dev/decisions.kb/small-bukzor-prefixed-packages.md
  - packages/bukzor-deadlock-damage/pyproject.toml
  - packages/bukzor-deadlock-lookup/pyproject.toml
  - apps/vis/server/src/vis_server/
  - packages/bukzor-deadlock-evaluator/docs/dev/claims.kb/architecture.kb/vis-timeline-seeds-compile-and-engage.md
  - apps/vis/docs/dev/claims.kb/server-workspace-python.md
---

# `bukzor-deadlock-damage`: vis's damage model moves into its package

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 2, beside 003, 004, 006)

## Problem Statement

Unit 001 left `packages/bukzor-deadlock-damage/` empty and wired: vis and
the evaluator already depend on it. Move the damage model into
`src/bukzor_deadlock_damage/`: the modules `timeline`, `measures`, `guns`,
`melee`, `casts` and `boons`, each with its `_test.py`, all from
`apps/vis/server/src/vis_server/`. vis keeps the protocol (`queries`, `http`,
`__main__`, `types`). Behavior does not change: the golden check proves it.

The import edges to cut (damage may depend on lookup and `bukzor_deadlock`,
never on vis):

- `measures` imports `Kind` from `vis_server/types.py`. `Kind` moves to
  damage, and vis imports it from there.
- `melee` and `casts` raise vis's `BadRequest`. Damage gets its own
  exception for "the input names nothing or can't be modeled", and vis turns
  it into `BadRequest` without changing a message byte. Settle the mechanism
  (a subclass, or a catch at the query boundary) and record it in Decisions.
- `casts` imports `names.property_label`, and `names` imports `melee` (for
  `MELEE`, the two pseudo-ability names). Move `load_tokens`,
  `property_label`, and the localization lookup inside `ability_name`, to
  `packages/bukzor-deadlock-lookup/src/bukzor_deadlock_lookup/names.py`
  (and `names_test.py`). In that package these two files are yours; unit 004
  owns the rest. The melee pseudo-names stay on the damage side, next to
  `melee.LIGHT` and `melee.HEAVY`. vis's `names.py` keeps only what is left,
  or goes away.
- `conftest.py` serves both sides (`within`, the synthetic trees). Split it
  by consumer; no helper exists in two copies.
- vis's `RELOAD_DIRS` gains the damage and lookup package directories.

The moved code now runs on Python 3.12 under the root's pyright; fix
3.13/3.14-only syntax only where the checks require it. Nothing in this unit
touches a `pyproject.toml` or a lock; if you need a dependency that is not
declared, stop and report.

Findings go to their homes:

- **VIS_SEED** (`vis-timeline-seeds-compile-and-engage.md`): its open
  question is ruled. The evaluator imports `bukzor-deadlock-damage`. Cite
  `docs/dev/decisions.kb/small-bukzor-prefixed-packages.md` as the owner's
  ruling, following that ledger's `CLAUDE.md`.
- **SERVER_PYTHON** (`server-workspace-python.md`): its "The cost"
  paragraph no longer holds. Rewrite it the same way.
- **Path references:** update every live reference to a moved module.
  `git grep` the moved file names across `docs/`, `apps/vis/docs/` and
  `.claude/ideas.kb/`; frozen records stay as they are. List any hit in
  `.claude/todo.md` in your Final report rather than editing it: the
  coordinator owns that file this wave.

**Scope (only these files):** `packages/bukzor-deadlock-damage/src/`,
`packages/bukzor-deadlock-lookup/src/bukzor_deadlock_lookup/names{,_test}.py`,
`apps/vis/server/src/`, `apps/vis/docs/`, the VIS_SEED claim,
`docs/dev/decisions.kb/vis-app.md` and other live `docs/` files that name a
moved module, `.claude/ideas.kb/`, and this file

## Steps

## Decisions

## Open Questions

## Final report
