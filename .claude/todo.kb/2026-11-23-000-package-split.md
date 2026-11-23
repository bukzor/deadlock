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

Only wave 1 touches a dependency list or a lock (beyond 003's one-line
wheel change): it scaffolds every new package, empty but wired, so each
later wave's units run in parallel on disjoint files. The rename touches
nearly every file, so it runs alone.

Wave 1:
- [x] [001 rename + scaffold](2026-11-23-000-package-split.kb/2026-11-23-001-rename.md): `deadlock` to `bukzor_deadlock`, `deadlock-evaluator` to `bukzor-deadlock-evaluator`, every live reference; then the four new packages, empty and wired

Wave 2 (parallel):
- [ ] [002 damage package](2026-11-23-000-package-split.kb/2026-11-23-002-damage-package.md): move vis's damage model into `bukzor-deadlock-damage`, and its localization helpers into the lookup's `names.py`
- [x] [003 dllscan package](2026-11-23-000-package-split.kb/2026-11-23-003-dllscan-package.md): `src/dllscan` into `bukzor-dllscan`
- [ ] [009 root depends on dllscan](2026-11-23-000-package-split.kb/2026-11-23-009-root-depends-on-dllscan.md): after 003, the root package declares the scanner it imports; the probes' imports follow
- [ ] [004 lookup API](2026-11-23-000-package-split.kb/2026-11-23-004-lookup-api.md): the lookup itself
- [x] [006 measurements package](2026-11-23-000-package-split.kb/2026-11-23-006-measurements-package.md): the Crimson Slash readings as YAML data apart from their code

Wave 3 (parallel):
- [ ] [005 adopt lookup](2026-11-23-000-package-split.kb/2026-11-23-005-adopt-lookup.md): damage and vis read the game data through the lookup
- [ ] [007 measurements check items](2026-11-23-000-package-split.kb/2026-11-23-007-measurements-check-items.md): item names and constant spirit investment checked against the lookup

Wave 4, on the owner's word that their edits to the root file are done:
- [ ] [008 retire root readings](2026-11-23-000-package-split.kb/2026-11-23-008-retire-root-readings.md): the owner's edits since `b9f93b9` carried into the YAML; the root `crimson_slash_test_data.py` removed

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
