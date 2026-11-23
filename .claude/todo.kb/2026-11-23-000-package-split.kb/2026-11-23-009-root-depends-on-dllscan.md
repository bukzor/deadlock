---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-23-003-dllscan-package.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - docs/dev/decisions.kb/small-bukzor-prefixed-packages.md
  - 2026-11-23-003-dllscan-package.md (its Open Questions only)
  - pyproject.toml
---

# The root package declares its dependency on `bukzor-dllscan`

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 2, after 003)

## Problem Statement

Unit 003 moved the scanner into `packages/bukzor-dllscan/`. The root package
(`bukzor-deadlock`) still imports `bukzor_dllscan` at runtime, in
`dll_load`, `dlls_*`, `registry_check` and `cvarlist_check`, but doesn't
declare it. That works in the workspace venv, but a built root wheel would
not import.

- **Declare the dependency.** Add `bukzor-dllscan` to the root
  `[project].dependencies`, with `bukzor-dllscan = { workspace = true }`
  under `[tool.uv.sources]`. Then run `uv lock` at the root and in
  `apps/vis/server`, since vis depends on the root package by path.
- **Update the decision record.** In the layout table of
  `docs/dev/decisions.kb/small-bukzor-prefixed-packages.md`, add
  `bukzor-dllscan` to the root row's "depends on" cell. That is the only
  edit to that file.
- **Repair the probes.** `docs/dev/probes/*.py` still `from dllscan import
  ...`. They are archived evidence, so change only the import names, and
  only enough that `python -c 'import ast; ...'`-level parsing and their
  imports resolve. Don't run them: they drive the live game.

Units 002 and 004 run beside you and touch no lock. The root lock and both
`pyproject.toml` files above are yours.

**Scope (only these files):** `pyproject.toml`, `uv.lock`,
`apps/vis/server/uv.lock`, `docs/dev/decisions.kb/small-bukzor-prefixed-packages.md`
(the root row's dependency cell), `docs/dev/probes/*.py` (import lines), and
this file

## Steps

- [x] Root `pyproject.toml`: dependency plus workspace source; `uv lock` at root and vis
- [x] Decision record: root row's "depends on" cell
- [x] Probes: import names only (6 files)

## Decisions

- Probe prose in `sentinel.py`'s docstring (`dllscan.registry`) renamed too, so it matches the import.

## Open Questions

- `docs/dev/probes/flags_cmdline.py` does `from bukzor_dllscan.__main__ import load_image`, but no `load_image` exists in the package (nor was it found in pre-split history I checked). Stale before this unit; left as is (archived evidence, imports otherwise resolve).

## Final report

- Root and vis locks regenerated (root +2 lines, vis +7: `bukzor-dllscan` added).
- Root pytest 1098 passed, pyright 0. Vis pytest 95 passed, basedpyright 0. Probes parse; every imported `bukzor_dllscan` module resolves except the `load_image` name above. Golden protocol not run: no vis code or data touched.
