---
managed-by: Skill(llm-subtask)
status: active
---

- [ ] Convert the remaining flat-path regex modules to `flatten.tree` (nested dicts), following `weapons.py`
  - [ ] `abilities.py` (`_BOUND`, `_DISABLED`, `_PROP`)
  - [ ] `ability_upgrades.py` (`_ENTITY`, `_UPGRADE`)
  - [ ] `heroes.py` (`_PATH`, `_ATTR`)
  - [ ] `item_bonuses.py` (`_ENTITY`, `_PROP`)
  - [ ] `items.py` (`_PRICE`, `_ENTITY`, `_COMPONENT`)
  - [ ] `levels.py` (`_PATH`)

## Later

We haven't (yet) decided where to place these in the task queue.
Please read and consider slotting them.

- [ ] Decide whether the flats stay a build stage at all, or tsv views read the `.vdata` directly (ADR; flats are local-only now, so their git-diffable-grain rationale no longer applies to them)
- [ ] Order the flats structurally at flatten time (sorted mapping keys, lists in index order) instead of `| LC_ALL=C sort` in `default.jsonl.do`, which puts `xs[10]` before `xs[2]`
