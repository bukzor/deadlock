---
managed-by: Skill(llm-subtask)
status: in-progress
---

# Package split: small `bukzor`-prefixed packages, one lookup API

**Design:** `docs/dev/decisions.kb/small-bukzor-prefixed-packages.md` (the
owner's rulings and the target layout; this plan only sequences it)
**Method:** Skill(subagent-handoffs); a sub-agent does each unit, briefed in
`2026-11-23-000-package-split.kb/`

## Problem Statement

Three consumers each read the game data their own way. `apps/vis/server`
loads its own trees and localization (`queries.load_data`,
`names.load_tokens`) and digs raw vdata keys by string (32 `dig` calls
across `boons`, `casts`, `guns`, `melee`, three private float parsers).
`packages/deadlock-evaluator` has no code; its ledger wants vis's damage
timeline but cannot import it across the 3.12/3.14 workspace split
(`architecture.kb/vis-timeline-seeds-compile-and-engage.md`).
`crimson_slash_test_data.py` names items in English, and the data has no
English-name lookup (item names live in the install's
`citadel_gc_mod_names` localization, which nothing loads).

## Waves

Each wave starts when the previous one is committed: every unit before the
last touches the root `pyproject.toml` or a `uv.lock`, which no two units
may share.

Wave 1:
- [ ] [001 rename](2026-11-23-000-package-split.kb/2026-11-23-001-rename.md): `deadlock` to `bukzor_deadlock`, `deadlock-evaluator` to `bukzor-deadlock-evaluator`, every live reference

Wave 2:
- [ ] [002 damage package](2026-11-23-000-package-split.kb/2026-11-23-002-damage-package.md): move vis's damage model to `packages/bukzor-deadlock-damage`; scaffold `packages/bukzor-deadlock-lookup`; wire vis and the evaluator to both

Wave 3 (parallel):
- [ ] [003 dllscan package](2026-11-23-000-package-split.kb/2026-11-23-003-dllscan-package.md): `src/dllscan` to `packages/bukzor-dllscan`
- [ ] [004 lookup API](2026-11-23-000-package-split.kb/2026-11-23-004-lookup-api.md): the lookup itself, inside the scaffold

Wave 4 (parallel):
- [ ] [005 adopt lookup](2026-11-23-000-package-split.kb/2026-11-23-005-adopt-lookup.md): damage and vis read the game data through the lookup
- [ ] [006 Crimson Slash calibration](2026-11-23-000-package-split.kb/2026-11-23-006-crimson-slash-calibration.md): the readings move into the evaluator, their item lists checked against the lookup

Byte-for-byte baseline of every vis query, captured before wave 1:
`trash/package-split/golden.before.txt`, from `golden.py` in the kb.

## Success Criteria

- [ ] `ls packages/` matches the decision's layout table; no `import deadlock`
  or `import dllscan` remains outside frozen handoff records
- [ ] `./bin/shell pytest` and `./bin/shell pyright` clean at the root;
  `uv run pytest` and `uv run basedpyright` clean in `apps/vis/server`
- [ ] `redo` rebuilds `data/` with no change to any committed TSV
- [ ] `vis-server query timeline hero=hero_yamato ability=<Crimson Slash's key>`
  prints the same bytes before and after the plan
- [ ] the damage modules hold no raw `dig` of a vdata key; vis holds no loader
