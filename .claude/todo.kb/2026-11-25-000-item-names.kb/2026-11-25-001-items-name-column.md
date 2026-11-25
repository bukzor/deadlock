---
managed-by: Skill(llm-subtask)
status: open
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../src/bukzor_deadlock/heroes.py
  - ../../../src/bukzor_deadlock/loc.py
  - ../../../src/bukzor_deadlock/paths.py
  - ../../../src/bukzor_deadlock/items.py
  - ../../../data/gamedata.dense.tsv/default.tsv.do
  - ../../../docs/dev/decisions.kb/sparse-views-with-defaults-sidecar.md
---

# `items.tsv`: an English `name` column

**Parent:** <https:../2026-11-25-000-item-names.md> (wave 1, its only unit)

## Problem Statement

A reader of `data/gamedata.tsv/items.tsv` sees `upgrade_critshot` and can't
tell that it is "Lucky Shot". Add the English in-game name, following the
precedent `heroes.tsv` already sets: a `name` column right after the key,
read with `loc.tokens`/`loc.look_up` from a localization file that `paths.py`
locates and `default.tsv.do` passes as an argument and tracks as a
dependency.

The source is `citadel_gc_mod_names/citadel_gc_mod_names_english.txt`, a
sibling directory of the hero-names file under
`game/citadel/resource/localization/`. It also has `<item>_search` tokens
(search aliases). Ignore them.

Decisions already made:

- The name goes only in `items.tsv`. `item_bonuses.tsv` and the
  `components` column keep codenames, joinable through `items.tsv`.
- An item with no token gets a blank name, not its codename and not an
  error. Disabled and infrastructure items are expected to lack names.

To settle and report: how many items that are *not* disabled lack a name,
and whether any of them name themselves through a vdata field rather than a
codename-keyed token. If they do, use that field, and record the finding in
`items.py`'s docstring.

Regenerate the committed view with `redo` (the dense view, then the sparse
`data/gamedata.tsv/items.tsv`, plus `items.defaults.tsv` if it changes).
Check: `grep 'Lucky Shot' data/gamedata.tsv/items.tsv` finds
`upgrade_critshot`.

**Scope (only these files):** `src/bukzor_deadlock/items.py`,
`src/bukzor_deadlock/items_test.py`, `src/bukzor_deadlock/paths.py`,
`src/bukzor_deadlock/paths_test.py`, `data/gamedata.dense.tsv/default.tsv.do`,
`data/gamedata.tsv/items.tsv`, `data/gamedata.tsv/items.defaults.tsv`, any
other `data/` build stamp the rebuild touches and that is already tracked,
and this handoff file.

## Steps

## Decisions

## Open Questions

## Final report
