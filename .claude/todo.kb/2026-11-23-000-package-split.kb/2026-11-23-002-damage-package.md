---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-001-rename.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - docs/dev/decisions.kb/small-bukzor-prefixed-packages.md
  - packages/bukzor-redotools/pyproject.toml
  - packages/bukzor-deadlock-evaluator/pyproject.toml
  - apps/vis/server/pyproject.toml
  - apps/vis/server/src/vis_server/
  - packages/bukzor-deadlock-evaluator/docs/dev/claims.kb/architecture.kb/vis-timeline-seeds-compile-and-engage.md
  - apps/vis/docs/dev/claims.kb/server-workspace-python.md
---

# `bukzor-deadlock-damage`: vis's damage model as its own package; the lookup scaffold

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 2, alone)

## Problem Statement

Move the damage model out of `apps/vis/server/src/vis_server/` into
`packages/bukzor-deadlock-damage/src/bukzor_deadlock_damage/`, a root-workspace
member shaped like `packages/bukzor-redotools`. The modules are `timeline`,
`measures`, `guns`, `melee`, `casts` and `boons`, each with its `_test.py`.
vis keeps the protocol (`queries`, `http`, `__main__`, `types`). Behavior
does not change: the golden check proves it.

Also scaffold `packages/bukzor-deadlock-lookup/` (distribution
`bukzor-deadlock-lookup`, import `bukzor_deadlock_lookup`, depending on
`bukzor-deadlock`), so the wave-3 lookup unit touches no lock. Its first
content is the localization half of `vis_server/names.py`.

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
  `bukzor_deadlock_lookup/names.py`. The melee pseudo-names stay on the
  damage side, next to `melee.LIGHT` and `melee.HEAVY`. vis's `names.py`
  keeps only what is left, or goes away.
- `conftest.py` serves both sides (`within`, the synthetic trees). Split it
  by consumer; no helper exists in two copies.

Wiring:

- Both new packages are root-workspace members; add them to
  `[tool.uv.sources]` wherever a member depends on them.
- The evaluator depends on both.
- vis depends on both by editable path, the way it already depends on
  `bukzor-deadlock`, and its `RELOAD_DIRS` gains both package directories.

The moved code now runs on Python 3.12 under the root's pyright; fix
3.13/3.14-only syntax only where the checks require it.

Findings go to their homes:

- **VIS_SEED** (`vis-timeline-seeds-compile-and-engage.md`): its open
  question is ruled. The evaluator imports `bukzor-deadlock-damage`. Cite
  the decision file as the owner's ruling, following that ledger's
  `CLAUDE.md`.
- **SERVER_PYTHON** (`server-workspace-python.md`): its "The cost"
  paragraph no longer holds. Rewrite it the same way.
- **Path references:** update every live reference to a moved module.
  `git grep` the module file names across `docs/`, `apps/vis/docs/`,
  `.claude/ideas.kb/` and `.claude/todo.md`; frozen records stay as they
  are.

**Scope (only these files):** `pyproject.toml`, `uv.lock`,
`packages/bukzor-deadlock-damage/` (new), `packages/bukzor-deadlock-lookup/`
(new), `packages/bukzor-deadlock-evaluator/pyproject.toml`, the VIS_SEED
claim, `apps/vis/server/` (`pyproject.toml`, `uv.lock`, `src/`),
`apps/vis/docs/`, `docs/dev/decisions.kb/vis-app.md`, other live `docs/`
files that name a moved module, `.claude/ideas.kb/`, `.claude/todo.md`, and
this file

## Steps

## Decisions

## Open Questions

## Final report
