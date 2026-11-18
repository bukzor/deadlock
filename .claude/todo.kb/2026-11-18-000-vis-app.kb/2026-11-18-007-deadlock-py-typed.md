---
managed-by: Skill(llm-subtask)
status: open
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
