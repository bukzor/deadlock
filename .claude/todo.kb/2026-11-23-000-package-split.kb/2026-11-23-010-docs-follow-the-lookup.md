---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-23-005-adopt-lookup.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - 2026-11-23-005-adopt-lookup.md (its Decisions and Open Questions)
  - packages/bukzor-deadlock-lookup/src/bukzor_deadlock_lookup/lookup.py
  - apps/vis/server/src/vis_server/queries.py
  - apps/vis/docs/dev/CLAUDE.md
---

# Docs that still describe vis's own loader follow the lookup

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 3, after 005)

## Problem Statement

Unit 005 removed vis's loader (`queries.load_data`, `GameData`, `listed`)
and the lookup's `names.py`, and moved their jobs onto the lookup
(`Lookup.playable`, `Lookup.label`, `load.load_tokens`). Four live docs
still describe the old code:

- **`docs/dev/decisions.kb/vis-app.md`**, lines 24 and 59, which name
  `bukzor_deadlock_lookup.names`.
- **`apps/vis/docs/dev/claims.kb/ability-names.md`**, which names `names.py`.
- **`apps/vis/docs/dev/claims.kb/hero-list.md`**, which names `listed`, now
  `Lookup.playable`.
- **`.claude/todo.md` line 44**, the item that plans to split `queries.py`.
  Its line counts and its seams (the `GameData`/`load_data`/`listed` seam)
  are now out of date. Re-measure `queries.py` and `queries_test.py`, with
  `wc -l` and with `black --diff` line counts, and restate the item from the
  current file. If the split is no longer needed, say so in the item; don't
  delete it.

State what each doc claims about the code as it now is. Keep each claim's
standing and its rationale, and follow the vis ledger's `CLAUDE.md` for claim
edits. Don't change the claims' meaning: only the code they point at
changed.

**Scope (only these files):** the four files above, and this file

## Steps

- [x] vis-app.md, ability-names.md, hero-list.md, todo.md item restated

## Decisions

- hero-list: `playable` filters on vdata `m_bDisabled` (via `bindings`), not the
  `heroes.tsv` `disabled` column; the claim's meaning is unchanged (same field),
  so I named the vdata field.
- todo.md: split is still needed (251/299 lines raw; 329/450 after black).

## Open Questions

None.

## Final report

Edited only the four docs plus this file. `llm.kb-validate apps/vis/docs/dev`:
36 files, 0 errors. No code changed, so pytest/pyright/golden are untouched.
