---
managed-by: Skill(llm-subtask)
status: done
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

- [x] `git mv` `src/dllscan/*` into `packages/bukzor-dllscan/src/bukzor_dllscan/` (the empty scaffold `__init__.py` replaced by the real one)
- [x] Module name `bukzor_dllscan` in the scanner, the root package's imports, `bin/winpy` (`PYTHONPATH`), `bin/winpy-facet.bash`, the `.do` recipes
- [x] Docs: `cvar-dump.kb/`, `own-the-dll-scanner.md`, the open plan `2026-11-05-000-per-dll-dump-tree.md` (`deadlock.*` -> `bukzor_deadlock.*` too)
- [x] Root wheel list drops `src/dllscan`; `uv lock` rewrote nothing
- [x] Checks, including `redo` on the DLL views

## Decisions

- `bin/winpy`'s `PYTHONPATH` is now `packages/bukzor-dllscan/src`: the scanner is the only thing the Windows side imports.
- Kept the CLI word `dllscan` for the shell function in `bin/winpy-facet.bash` and for prose naming the tool (`dllscan registry` in `cvar-dump.kb`); every module-name use (`bin/winpy MODULE`, `python -m`, dotted names, paths, argparse `prog`) is `bukzor_dllscan`.
- Did not add `bukzor-dllscan` to the root `dependencies`: the brief limits `pyproject.toml` to the wheel list. See Open Questions.

## Open Questions

- The root package imports `bukzor_dllscan` at runtime (`dll_load`, `dlls_*`, `registry_check`, `cvarlist_check`) but declares no dependency on it, and its wheel no longer ships it. Works in the workspace venv (`uv sync --all-packages`); a built root wheel would not. Fix is `"bukzor-dllscan"` in `[project].dependencies` plus `bukzor-dllscan = { workspace = true }` in `[tool.uv.sources]`.
- `docs/dev/probes/*.py` (archived experiment scripts, outside this brief's scope) still `from dllscan import ...`; they no longer import.

## Final report

- Moved by `git mv`: 28 files (`__init__.py` shows as modify/delete against the scaffold's empty one). Edits beyond the move are names only (imports, docstrings, `prog=`, `stdlib_only_test.py`'s allowed-name set).
- `./bin/shell pytest`: 902 passed. `./bin/shell pyright`: 2 errors, both in the sibling's `bukzor_deadlock_measurements/load_test.py` (not this unit's). Vis `uv run pytest` 239 passed, `basedpyright` clean; golden protocol `cmp`-identical to `golden.before.txt`.
- Windows host works here. `redo` of `data/dlls/{file,load,convars,concommands}.tsv`, `load.tree.txt`, `data/dlls.check/{concommands,convars,registry}` succeeded; `git status --short -- data/` showed no committed view changed (only the known `deadlock-version.json` drift, restored). `registry`: all match (server 2008/493, client 2289/428).
- Note: `redo` refused `data/deadlock-version.json` ("you modified it") after an earlier `git checkout` of it; deleting it first let redo rebuild it, then I restored it.
- `.claude/todo.md` hits: line 6 (`dllscan` as a package name, fine) and line 43 (`src/dllscan/registry.py` now `packages/bukzor-dllscan/src/bukzor_dllscan/registry.py`). Not edited.
- `.claude/todo.kb/2026-11-23-000-package-split.md` lines 38 and 55 mention `src/dllscan` / `import dllscan` (parent plan; not mine).
