---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - ./CLAUDE.md
---

# `deadlock` package: declare its inline types (`py.typed`)

**Parent:** <https:../2026-11-18-000-vis-app.md> (wave 1)

## Problem Statement

`apps/vis/server` imports the root `deadlock` package, and basedpyright `all`
reports `reportMissingTypeStubs` on each of those imports because
`src/deadlock/py.typed` is missing. Add the empty marker. Check that the root
package's build includes it (`pyproject.toml` at the repo root, hatch or
whatever builds it). Then confirm both checks:
- `uv run basedpyright src/vis_server/melee.py src/vis_server/melee_test.py`,
  run in `apps/vis/server`, reports 0 errors;
- the root project's own `./bin/shell pyright` result is unchanged.

If marking the package typed brings out new errors in `apps/vis/server` files
other than `melee*`, list them in the Final report. Don't fix them: those files
belong to sibling units.

**Scope (only these files):** `src/deadlock/py.typed`, plus the root
`pyproject.toml` only if the build needs it to ship the marker

## Steps

- [x] Baseline: root `./bin/shell pyright` 0 errors; vis-server `basedpyright` 15
  errors (13 `reportMissingTypeStubs`, 2 others).
- [x] Add empty `src/deadlock/py.typed`.
- [x] Re-run checks; build a wheel to confirm the marker ships.

## Decisions

- Root `pyproject.toml` left alone: hatch's `packages = ["src/deadlock"]`
  includes every file in the directory (the built wheel lists
  `deadlock/py.typed`). The vis server's editable install is a `.pth` pointing
  at `src/`, so it sees the marker without a reinstall.

## Open Questions

None.

## Final report

- `melee.py` + `melee_test.py` basedpyright: 0 errors, 0 warnings.
- Root `./bin/shell pyright`: 0 errors before, 0 errors after.
- All 13 `reportMissingTypeStubs` in `apps/vis/server` are gone. Marking the
  package typed brought out no new errors. Two errors were already present
  before this change, and both belong to sibling units (not fixed):
  - `casts.py:142:13` reportImplicitStringConcatenation
  - `casts_test.py:23:5` type of `wrapped` is partially unknown
- No deviations from the brief.
