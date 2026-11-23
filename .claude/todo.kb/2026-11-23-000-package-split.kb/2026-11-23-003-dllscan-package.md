---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-23-001-rename.md
required-reading:
  - .claude/todo.kb/2026-11-23-000-package-split.kb/CLAUDE.md
  - docs/dev/decisions.kb/small-bukzor-prefixed-packages.md
  - docs/dev/decisions.kb/own-the-dll-scanner.md
  - docs/dev/cvar-dump.kb/windows-python-host.md
  - bin/winpy-facet.bash
  - packages/bukzor-dllscan/pyproject.toml
---

# `bukzor-dllscan`: the DLL scanner moves into its package

**Parent:** <https:../2026-11-23-000-package-split.md> (wave 2, beside 002, 004, 006)

## Problem Statement

Unit 001 left `packages/bukzor-dllscan/` empty and wired. Move `src/dllscan/`
into `packages/bukzor-dllscan/src/bukzor_dllscan/`. It stays stdlib-only
(`stdlib_only_test.py` guards that). The root wheel stops shipping
`src/dllscan` (root `pyproject.toml`, the wheel's `packages` list).

The scanner runs in a Windows-host Python that gets the source files, not
an installed package (`bin/winpy-facet.bash` gathers `src/dllscan/*.py`).
Every caller follows the new path and the new module name, `bukzor_dllscan`:

- `bin/winpy-facet.bash`, `bin/winpy` if it names the module
- the `data/dlls*/**/*.do` recipes (their `dllscan` calls and their
  dependency lists on `document.py`)
- the root package's own imports of the scanner, if any (check)
- `docs/dev/cvar-dump.kb/`, `docs/dev/decisions.kb/own-the-dll-scanner.md`
- the open plan `.claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md` (not
  its frozen `.kb/` records). Unit 001 also left `deadlock.*` names there,
  and in the scanner's own comments and `stdlib_only_test.py`. Make those
  `bukzor_deadlock.*` as you go.

Leave the CLI word `dllscan` in shell function names and prose only where
it means the tool rather than the module. List any hit in
`.claude/todo.md` in your Final report rather than editing it: the
coordinator owns that file this wave.

Extra check, on top of the kb's: rebuild the DLL views (`redo` on the
`data/dlls/` and `data/dlls.check/` targets the recipes name), and
afterwards `git status --short -- data/` shows no committed file changed.
If the Windows host can't run here, say so and check the rest.

Siblings run beside you on other packages. The root `pyproject.toml` and
`uv.lock` are yours alone this wave; change nothing in them beyond the
wheel list (and whatever `uv lock` then rewrites).

**Scope (only these files):** `pyproject.toml`, `uv.lock`, `src/dllscan/` →
`packages/bukzor-dllscan/src/bukzor_dllscan/`, `bin/`, `data/dlls/**/*.do`,
`data/dlls.check/**/*.do`, the root package's imports of the scanner,
`docs/dev/cvar-dump.kb/`, `docs/dev/decisions.kb/own-the-dll-scanner.md`,
`.claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md`, and this file

## Steps

## Decisions

## Open Questions

## Final report
