---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-007-measurements-check-items.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - docs/dev/decisions.kb/small-bukzor-prefixed-packages.md (the measurements row and its ruling)
  - packages/bukzor-deadlock-measurements/
  - packages/bukzor-dllscan/src/bukzor_dllscan/stdlib_only_test.py (the import-guard pattern)
---

# Measurements: the readings as Python data over a frozen-dataclass vocabulary

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 4)

## Problem Statement

The owner ruled that the raw readings are Python, not YAML. The ruling is
quoted in the decision file, under its measurements reason. Rebuild the data half of
`packages/bukzor-deadlock-measurements/` to match:

- **Vocabulary:** `records.py` holds only `@dataclass(frozen=True,
  kw_only=True)` classes, plus type aliases. Their only methods are pure
  `@property` derivations over their own fields (`heal`, `echo_heal`). It
  imports only `dataclasses`, `typing` and `collections.abc`. Both the data
  and the programs import it.
- **Data:** `src/bukzor_deadlock_measurements/experiments/`, with one module
  per experiment, starting with `crimson_slash.py`. Each module imports only
  from `records` and binds one top-level `EXPERIMENT`. Carry every reading
  over exactly as `data/crimson-slash.yaml` states it, and move its comments
  (procedure, setup, the regen note) to the data module's docstring and
  comments. Keep it easy to edit by hand, the way the owner's own
  `crimson_slash_test_data.py` at the repo root reads. Read that file but
  don't edit it.
- **Guard:** `layering_test.py` checks both rules from the AST, the way
  `stdlib_only_test.py` does. It also has its own tests that feed a
  violation of each kind (a plain function in `records`, a non-frozen
  dataclass, an experiment module importing `check`) and see it flagged.
- **Programs:** `load.py` discovers the experiment modules (for example with
  `pkgutil`) and returns their `EXPERIMENT`s. `check.py` and `summary.py`
  keep their behavior. `python -m bukzor_deadlock_measurements` prints the
  same table, byte for byte (`cmp` it before and after).
- **Subtract:** remove `data/` (the YAML and `readings.schema.json`), the
  `jsonschema` and `pyyaml` dependencies (then run `uv lock` at the root and
  in `apps/vis/server`), and every schema-validation path. Make the
  package's `description` and README match. The decision file already
  states the target; don't edit it.

No other unit runs this wave, so the root lock is yours.

**Scope (only these files):** `packages/bukzor-deadlock-measurements/`,
`uv.lock`, `apps/vis/server/uv.lock`, and this file

## Steps

## Decisions

## Open Questions

## Final report
