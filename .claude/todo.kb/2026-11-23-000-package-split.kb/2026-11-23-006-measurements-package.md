---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-001-rename.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - crimson_slash_test_data.py as of b9f93b9 (`git show b9f93b9:crimson_slash_test_data.py`)
  - trash/crimson_slash_test_data.md (the owner's hand-written original)
  - ~/.claude/reference.kb/data-format-selection.md
  - packages/bukzor-deadlock-measurements/pyproject.toml
  - packages/bukzor-deadlock-evaluator/docs/dev/claims.kb/architecture.kb/measure-is-the-ground-truth-loop.md
  - packages/bukzor-deadlock-evaluator/docs/dev/CLAUDE.md
---

# `bukzor-deadlock-measurements`: sandbox readings as data, apart from their code

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 2, beside 002, 003, 004)

## Problem Statement

`crimson_slash_test_data.py` at the repo root mixes two activities. Work
from its snapshot at commit `b9f93b9`, never the working-tree file: the
owner keeps editing that one, and it is not yours to touch. The
owner hand-edits readings from live sandbox runs into it, and it also holds
the code that types those readings, derives heals from them and prints a
summary. Split it into the package unit 001 left empty and wired,
`packages/bukzor-deadlock-measurements/`.

- **Data:** one hand-authored YAML file per experiment (the reference's
  rule for nested, hand-edited data; the owner's original was YAML too),
  starting with Crimson Slash's. Scenarios stay grouped under the dummy
  they ran against. Ship a JSON Schema for the readings, and point the YAML
  at it with a `yaml-language-server` comment, so an editor checks a hand
  edit as it's typed. Keep the data in the package, outside `src/`, and
  record where and why: the repo's `data/` is generated output, so it
  doesn't belong there.
- **Code:** in `src/bukzor_deadlock_measurements/`, the typed records (the
  current dataclasses), a loader that validates each file and builds them,
  and the summary table. Keep `python -m bukzor_deadlock_measurements`
  printing it for every experiment.
- **Readings are observations, not lookups.** Carry every recorded number
  over exactly as the snapshot states it. `cmp` the summary table's output
  against the snapshot's (`git show` it into your trash dir and run it).
- **The comment on regen is unsourced.** "Repeated measurements disagreed;
  these are the values that each recurred" appears nowhere in the owner's
  original. Keep its meaning beside the data, and list it in Open Questions
  for the owner.
- **No game-data checks yet.** Unit 007 checks the item names against the
  lookup next wave.

Unit 001 left a placeholder `description` in the package's
`pyproject.toml`; write the real one (that field is yours; the dependencies
are not).

Leave the root `crimson_slash_test_data.py` in place, and reference neither
it nor the snapshot from the package. Unit 008 carries over the owner's
later edits and retires it. Record the package in the evaluator ledger, as the ledger's `CLAUDE.md`
says, as the first data for its "measure" loop. Don't edit the VIS_SEED
claim: unit 002 owns it this wave.

**Scope (only these files):** `packages/bukzor-deadlock-measurements/` (except its `pyproject.toml`
dependencies), one new or edited entry in the evaluator's `docs/dev/claims.kb/`
(not VIS_SEED), and this file

## Steps

## Decisions

## Open Questions

## Final report
