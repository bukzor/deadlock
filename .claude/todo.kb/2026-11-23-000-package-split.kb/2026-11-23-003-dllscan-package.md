---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-002-damage-package.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - docs/dev/decisions.kb/small-bukzor-prefixed-packages.md
  - docs/dev/decisions.kb/own-the-dll-scanner.md
  - docs/dev/cvar-dump.kb/windows-python-host.md
  - bin/winpy-facet.bash
  - packages/bukzor-redotools/pyproject.toml
---

# `bukzor-dllscan`: the DLL scanner as its own package

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 3, beside unit 004)

## Problem Statement

Move `src/dllscan/` to `packages/bukzor-dllscan/src/bukzor_dllscan/`, a
root-workspace member shaped like `packages/bukzor-redotools`, with no
runtime dependencies. It stays stdlib-only (`stdlib_only_test.py` guards
that). The root wheel stops shipping `dllscan`.

The scanner runs in a Windows-host Python that gets the source files, not
an installed package (`bin/winpy-facet.bash` gathers `src/dllscan/*.py`).
Every caller follows the new path and the new module name, `bukzor_dllscan`:

- `bin/winpy-facet.bash`, `bin/winpy` if it names the module
- the `data/dlls*/**/*.do` recipes (their `dllscan` calls and their
  dependency lists on `document.py`)
- the root package's own imports of the scanner, if any (check)
- `docs/dev/cvar-dump.kb/`, `docs/dev/decisions.kb/own-the-dll-scanner.md`,
  `.claude/todo.md`

Leave the CLI word `dllscan` in shell function names and prose only where
it means the tool rather than the module.

Extra check, on top of the kb's: rebuild the DLL views (`redo` on the
`data/dlls/` and `data/dlls.check/` targets the recipes name), and
afterwards `git status --short -- data/` shows no committed file changed.
If the Windows host can't run here, say so and check the rest.

Unit 004 runs alongside you. It owns `packages/bukzor-deadlock-lookup/`
and touches no lock, so the root `uv.lock` is yours alone.

**Scope (only these files):** `pyproject.toml`, `uv.lock`, `src/dllscan/` →
`packages/bukzor-dllscan/`, `bin/`, `data/dlls/**/*.do`,
`data/dlls.check/**/*.do`, the root package's imports of the scanner,
`docs/dev/cvar-dump.kb/`, `docs/dev/decisions.kb/own-the-dll-scanner.md`,
`.claude/todo.md`, and this file

## Steps

## Decisions

## Open Questions

## Final report
