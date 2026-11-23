---
managed-by: Skill(llm-subtask)
status: open
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
`trash/package-split/model.before.txt` (captured before this unit): `cmp`
it. The model's other lines are the owner's: don't edit, move or reformat
them.

Then `git rm` the root data file. The package's checks (item names, constant
spirit investment) must pass on the carried-over data. A failure there is a
finding for the owner, not something to fix by editing a reading.

**Scope (only these files):** `crimson_slash_test_data.py` (removed),
the import line of `crimson_slash_model.py`,
`packages/bukzor-deadlock-measurements/`, and this file

## Steps

## Decisions

## Open Questions

## Final report
