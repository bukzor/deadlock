---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-011-measurements-data-as-python.md
  - the owner's word that their edits to the root crimson_slash_test_data.py are finished
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

Then `git rm` the root file. The package's checks (item names, constant
spirit investment) must pass on the carried-over data. A failure there is a
finding for the owner, not something to fix by editing a reading.

**Scope (only these files):** `crimson_slash_test_data.py` (removed),
`packages/bukzor-deadlock-measurements/`, and this file

## Steps

## Decisions

## Open Questions

## Final report
