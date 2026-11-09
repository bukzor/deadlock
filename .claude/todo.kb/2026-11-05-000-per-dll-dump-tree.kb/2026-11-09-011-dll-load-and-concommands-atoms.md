---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-09-010-dll-file-facet.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-008-dllscan-main-load-concommands-strides.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-009-dll-inventory-and-dlls-list.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-010-dll-file-facet.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/convar-dump.kb/dll-coverage.md
---

# `deadlock.dll_load`, the `load` and `concommands` atoms

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Wave 6; row
`dll_load`, facets `load` and `concommands`)

## Problem Statement

The Windows-side atoms. **Start once 010 is done:** it settles the `.do`
shape and the shared basename → path lookup. Reuse both.

- **`deadlock.dll_load`:** `EXCLUDED: dict[basename, reason]` for DLLs never
  to load. `helpsystem`, `assetpreview`, `propertyeditor` and
  `toolframework2` hang `LoadLibrary` with an unkillable process (6851).
  Unit 007 checked the static + delay-import closure of all 97 DLLs on 6860:
  only those four reach a hang-listed DLL. It writes the `excluded`
  `LoadExcluded` document WSL-side.
  `phonon4` and `vfx_dx11` *fail* (`LoadLibraryExW: 126`). That is data (a
  `failed` document from `dllscan`), not an exclusion.
- **`data/dlls/load/default.json.do`:** the guard as in 010. An excluded DLL
  gets the WSL-side record. Anything else runs `bin/winpy dllscan load …`,
  with the invocation from 008's Final report. Dependencies: `dlls.list`,
  the DLL file, `src/dllscan/*.py`, `bin/winpy`, and `dll_load.py`.
- **`data/dlls/concommands/default.json.do`:** the guard plus
  `load/$2.json` must say `ok`. Anything else fails loudly, naming the
  outcome. Then `bin/winpy dllscan concommands …`. Same dependencies, plus
  the `load` document.
- **Timeout:** `bin/winpy`'s default is 60 s. `nvngx_dlss.dll` takes ~15 s
  per `find_queues` pass (007), so one pass fits. Leave the default unless
  measurement says otherwise.

**Real run:** `redo -j8` every `load` atom over all 97 DLLs (list them from
`dlls.list`), then every `concommands` atom for the `ok` ones. Report:
- the outcome counts (expect 91 ok, 2 failed, 4 excluded on 6860);
- the total command count (007 counted 1411 strict);
- wall time;
- whether a second `redo` re-runs nothing;
- whether a forced rebuild is byte-identical.

**Scope:** `src/deadlock/dll_load.py` (+ test), the two `.do` files.

## Steps

- [~] `dll_load_test.py` against a stub: red
- [ ] `dll_load.py`: green; mutants killed
- [ ] `load` and `concommands` `.do` files; pytest, pyright
- [ ] Real run (6860): all `load`, then the `ok` `concommands`

## Decisions

## Open Questions

## Final report
