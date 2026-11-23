---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-004-lookup-api.md
  - 2026-11-23-006-measurements-package.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - packages/bukzor-deadlock-measurements/
  - packages/bukzor-deadlock-lookup/src/
  - 2026-11-23-004-lookup-api.md (its Decisions and Open Questions only)
  - 2026-11-23-006-measurements-package.md (its Decisions and Open Questions only)
---

# Sandbox measurements check their item lists against the game data

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 3, beside unit 005)

## Problem Statement

The measurements loader (unit 006) builds typed records from the hand-edited
YAML. Make it check them against the game data through the lookup
(unit 004):

- **Item names:** every name in an item list resolves to an item. The
  failure names the scenario and the near candidates.
- **Spirit investment:** it is held constant across a dummy's scenarios.
  Assert that each scenario's spirit items cost the same total as its
  dummy's baseline.
- **Item lists as written:** take them as the file states them; the owner
  corrects them by hand.

**Readings are observations, not lookups.** Never replace or default a
recorded number from the data. The sandbox dummy's 10686 health differs
from the data's `hero_targetdummy` (2990), because the sandbox configures
its dummies.

Two repairs to unit 006's package, routed from its report:

- **The schema is the one home of the readings' shape.** `load.py`
  re-checks shape by hand, mirroring `data/readings.schema.json`, because
  `jsonschema` was not a declared dependency. Add `jsonschema` to the
  package's dependencies (`uv add --package bukzor-deadlock-measurements
  jsonschema` from the repo root, which rewrites the root lock; the lock is
  yours this wave). Validate each file against the schema, and delete the
  hand-written mirror. A schema violation's message still names the file and
  the offending path.
- **No code in `__init__.py`** (`~/.claude/reference.kb/python/style.md`):
  it re-exports eleven names. Empty it, and import from the defining
  modules.

Add a test beside the loader that runs the checks on the real experiment
files, and one that feeds a misspelled item and an unequal swap and sees
each fail. Use only the lookup's public API. If it lacks something, report
it rather than editing the lookup: unit 005 owns that package this wave.

**Scope (only these files):** `packages/bukzor-deadlock-measurements/src/`,
its `pyproject.toml`, the root `uv.lock`, and this file

## Steps

## Decisions

## Open Questions

## Final report
