---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-001-rename.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - crimson_slash_test_data.py
  - trash/crimson_slash_test_data.md (the owner's hand-written original)
  - ~/.claude/reference.kb/data-format-selection.md
  - packages/bukzor-deadlock-measurements/pyproject.toml
  - packages/bukzor-deadlock-evaluator/docs/dev/claims.kb/architecture.kb/measure-is-the-ground-truth-loop.md
  - packages/bukzor-deadlock-evaluator/docs/dev/CLAUDE.md
---

# `bukzor-deadlock-measurements`: sandbox readings as data, apart from their code

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 2, beside 002, 003, 004)

## Problem Statement

`crimson_slash_test_data.py` at the repo root mixes two activities. The
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
  over exactly as the file states it, including the owner's latest edits.
  `cmp` the summary table's output before and after the split.
- **The comment on regen is unsourced.** "Repeated measurements disagreed;
  these are the values that each recurred" appears nowhere in the owner's
  original. Keep its meaning beside the data, and list it in Open Questions
  for the owner.
- **No game-data checks yet.** Unit 007 checks the item names against the
  lookup next wave.

Delete the root `crimson_slash_test_data.py` (`git mv` it to the data or
code file, whichever keeps more of its lines, so git pairs the rename).
Record the package in the evaluator ledger, as the ledger's `CLAUDE.md`
says, as the first data for its "measure" loop. Don't edit the VIS_SEED
claim: unit 002 owns it this wave.

**Scope (only these files):** `crimson_slash_test_data.py` (removed),
`packages/bukzor-deadlock-measurements/` (except its `pyproject.toml`
dependencies), one new or edited entry in the evaluator's `docs/dev/claims.kb/`
(not VIS_SEED), and this file

## Steps

## Decisions

## Open Questions

## Final report
