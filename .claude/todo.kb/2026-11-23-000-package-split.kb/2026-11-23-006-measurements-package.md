---
managed-by: Skill(llm-subtask)
status: done
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

- [x] Snapshot at b9f93b9 into trash/006; capture its table
- [x] `data/crimson-slash.yaml` + `data/readings.schema.json`
- [x] records, loader, summary, `__main__`, tests
- [x] `cmp` table against snapshot: identical
- [x] real `description`; README (where/why data lives); ledger edit
- [x] pytest, pyright, golden clean

## Decisions

- Data at `packages/bukzor-deadlock-measurements/data/`, outside `src/`;
  schema as `readings.schema.json`. Rationale is in the package README.
- The docstring's setup/procedure prose became comments atop the YAML
  (not schema fields): it is a note for the human editor, not a reading.
- Items listed in full per scenario, no YAML anchor for BASE_ITEMS (clearer
  for hand edits).
- Loader validates by hand, mirroring the schema's shape (unknown/missing
  keys, types): `jsonschema` is not a declared dependency and the
  dependency list is not mine.
- Ledger: appended a paragraph to `measure-is-the-ground-truth-loop.md`
  rather than adding a claim (standing unchanged, `agent`).

## Open Questions

- Owner: the regen comment "Repeated measurements disagreed; these are the
  values that each recurred" is unsourced (not in the owner's original).
  Kept beside the data in the YAML and in the schema's `regen` description.
- Should `jsonschema` become a dependency so the loader validates against the
  schema file itself (one source of truth) instead of a mirrored hand check?
- The wheel excludes `data/`, so the loader works from a checkout/editable
  install only. Acceptable until something installs it elsewhere?
- Mid-unit I ran a bare `git stash` then `git stash pop` (a slip): siblings'
  tracked edits were reverted for a few seconds and restored, but staged
  (index) modifications of tracked files came back unstaged. Worktree
  content is intact; siblings should re-stage.

## Final report

Checks: table `cmp` identical to the snapshot's; root pytest 902 passed;
pyright 0 errors; vis golden `cmp` identical. (An earlier full pytest run
showed one dllscan `stdlib_only_test` failure, a sibling's in-flight work;
it passed on rerun.) Results: package under
`packages/bukzor-deadlock-measurements/` (data/, README.md, src/); ledger
edit in the evaluator's `architecture.kb/measure-is-the-ground-truth-loop.md`.
