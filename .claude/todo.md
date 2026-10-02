---
managed-by: Skill(llm-subtask)
status: active
---

- [x] Convert the remaining flat-path regex modules to `flatten.tree` (nested dicts), following `weapons.py`; fix each module's stale "committed, flattened" docstring (flats are local-only) as it's touched
  - [x] `items.py` (`_PRICE`, `_ENTITY`, `_COMPONENT`)
  - [x] `levels.py` (`_PATH`)
  - [x] `abilities.py` (`_BOUND`, `_DISABLED`, `_PROP`)
  - [x] `item_bonuses.py` (`_ENTITY`, `_PROP`)
  - [x] `ability_upgrades.py` (`_ENTITY`, `_UPGRADE`)
  - [x] `heroes.py` (`_PATH`, `_ATTR`)
  - [x] `weapons.py` docstring only (already converted)
- [ ] Think through a revamp of validation and error handling: assert wherever a change would make output quietly wrong or trivial, handle (normalize, blank cell) wherever it is merely different
  - [ ] Leading design to test: creation stays lenient and total; judgment moves to separate redo targets that write findings as data (`data/gamedata.check/<subject>.findings.tsv`, one row per violation, empty when clean), and `all.do` fails if any are non-empty (redo discards a failed target's output, so a failing check leaves nothing to inspect)
  - [ ] Two subject kinds: source-shape checks (depend on flats only) and view-output checks (depend on the view's TSV: empty table, all-blank column)
  - [ ] Inventory every assertion and special case in `src/deadlock/` and sort it: our own parser is wrong (stays in creation) / quiet-wrongness canary (becomes a finding) / over-specific (handled)
  - [ ] Known gaps to cover: signature slot-prefix rename gives an empty table silently; `m_bDisabled` can serialize as bool/`"true"`/`1` (`items._truthy` normalizes, heroes/weapons do not); renamed `m_strValue`/`AbilityCooldown` gives all-blank cooldowns; renamed `EAbilityPoints` gives an all-zero AP column; a blank hero stat is ambiguous (hero-unique vs dropped) but decidable via `_base`: assert a hero's stats are a superset of its `_base`'s (check what `_base` holds, and whether chains exist)
  - [ ] Pre-commit gap: building a single view directly skips the gate; decide whether a pre-commit step runs it

## Later

We haven't (yet) decided where to place these in the task queue.

- [ ] Flats ordering: drop `| LC_ALL=C sort` in `default.jsonl.do` (`leaves` already yields source order; `unflatten` is order-independent; sort puts `xs[10]` before `xs[2]` and loses key order). Also fix the `gamedata.py:12` comment
