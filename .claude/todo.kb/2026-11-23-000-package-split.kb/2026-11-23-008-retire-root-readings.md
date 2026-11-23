---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-23-011-measurements-data-as-python.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - packages/bukzor-deadlock-measurements/
  - 2026-11-23-011-measurements-data-as-python.md (its Decisions and Open Questions only)
---

# Carry the owner's later edits into the measurements data; retire the root file

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 5, alone)

## Problem Statement

Units 006 and 011 built the readings in `packages/bukzor-deadlock-measurements/`,
as a Python experiment module, from a snapshot of `crimson_slash_test_data.py` at commit `b9f93b9`. The
owner kept editing the root file after that snapshot.

`git diff b9f93b9 -- crimson_slash_test_data.py` shows the owner's later
edits, both committed and uncommitted. Carry every reading, item list and
comment they changed into the package's experiment module. If an edit is to code (types,
derived values, the table), apply its intent to the package's code. Record
each carried-over edit in Decisions, and anything you couldn't map in Open
Questions.

**The owner's vocabulary wins.** Their final file reshapes the records:
`Health`, `Scenario` (with `heal` and `echo_heal`), `Dummy`, and
`ExperimentalSetup`, bound as `SETUPS`, with new field names and three
setups. Make the package's `records.py` and experiment module say what the
owner's file says, keeping its class and field names; they fit the
strict-vocabulary rule (`layering_test.py`). `load`, `check` and `summary`
follow the new shape. The summary table changes with the data: that's
expected. If a record of the owner's breaks the rule, report it rather than
changing their code.

**The owner's model is a consumer.** `crimson_slash_model.py`, at the repo
root, imports `SETUPS`, `ExperimentalSetup` and `Scenario` from the root data
file. Change only that import line, to import from the package. Then
`./bin/shell python crimson_slash_model.py` must print exactly
`trash/package-split/model.before.txt` on stdout (captured before this unit,
stdout only): `cmp` it. The model's other lines are the owner's: don't edit, move or reformat
them.

Then `git rm` the root data file. The package's checks (item names, constant
spirit investment) must pass on the carried-over data. A failure there is a
finding for the owner, not something to fix by editing a reading.

**Scope (only these files):** `crimson_slash_test_data.py` (removed),
the import line of `crimson_slash_model.py`,
`packages/bukzor-deadlock-measurements/`, and this file

## Steps

- [x] Port the owner's records (`Health`, `Scenario`, `Dummy`, `ExperimentalSetup`) into `records.py`
- [x] Port the owner's `SETUPS` and docstring into `experiments/crimson_slash.py`
- [x] `load`, `check`, `summary`, `layering_test`, tests, README follow the new shape
- [x] Repoint the model's import; `cmp` its stdout with `model.before.txt`
- [x] `git rm` the root data file; all checks; commit

## Decisions

- Carried the owner's final file verbatim, not edit by edit: `records.py`
  is its four classes (field comments included) under the package docstring;
  `experiments/crimson_slash.py` is its docstring (only the "Run ..." line
  repointed to `python -m bukzor_deadlock_measurements`) and its `SETUPS`,
  `diff`-identical. That carries every later edit: `Health.hit`/`reverb`
  (for `initial`/`after`), `Scenario.health`/`damage` (for `hero`/
  `damage_popups`), `Hero` dropped (spirit moved to `ExperimentalSetup`),
  setup-common items split from per-scenario items, readings 1337->1336 and
  199->198, the 9091-hp dummy and the 116-spirit "Improved Spirit" setup,
  per-condition `regen` comments, the procedure and damage-rounding text.
- `Experiment` (with its `name`) is gone: the owner's shape has none. An
  experiment module binds `SETUPS`; `load_all()` returns them keyed by module
  name (`load.Experiments`); `check(name, setups, lookup)` reports
  `name.SETUPS[n] ('scenario')`; the layering rule now demands `SETUPS`.
- `check` costs a scenario's spirit items as `setup.items + scenario.items`,
  matching the owner's "held constant within an ExperimentalSetup". Added
  `it_names_a_misspelled_setup_item` (seen red with the name corrected); the
  non-spirit swap test now swaps in the setup's items, where Healbane lives.
- `summary` is the owner's `format_row`/header (column `damage`, not
  `popups`); `python -m bukzor_deadlock_measurements` prints exactly what the
  owner's `python crimson_slash_test_data.py` printed.
- The model's one import line became two (`SETUPS` from the experiment
  module, the types from `records`), its only edit.

## Open Questions

- `crimson_slash_model.py`'s docstring (line 8) still says it compares with
  `crimson_slash_test_data.py`; outside my scope (import line only). The
  owner may want it to name `bukzor_deadlock_measurements`.

## Final report

All clean: package checks pass on the carried-over data (items resolve,
spirit cost constant in all three setups); `crimson_slash_model.py` stdout
`cmp`-equal to `trash/package-split/model.before.txt`
(`trash/unit-008/model.after.txt`); root `pytest`, `pyright`; vis `pytest`,
`basedpyright`; golden `cmp`-equal. The summary table now equals the owner's
own table (`trash/unit-008/table.after.txt`). Root
`crimson_slash_test_data.py` removed with `git rm`. Results live in
`packages/bukzor-deadlock-measurements/` (`records.py`,
`experiments/crimson_slash.py`, `load.py`, `check.py`, `summary.py`, tests,
README) and the model's import. Deviation: the import is two lines, not one.
