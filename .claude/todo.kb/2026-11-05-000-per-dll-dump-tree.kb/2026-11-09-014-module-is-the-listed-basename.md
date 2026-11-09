---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-008-dllscan-main-load-concommands-strides.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-009-dll-inventory-and-dlls-list.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-012-dlls-facet-aggregates.md
---

# A document's `module` is the DLL's basename as listed

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the facet
documents; 012's Open Question on `module`)

## Problem Statement

`document.py` defines `module` as the DLL's basename as it appears in
`data/dlls.list`, which is the case it has on disk (`Qt5Core.dll`). But
`dllscan.facets.concommands` lowercases it, and `deadlock.dlls_concommands`
works around that by comparing both sides lowercased. Make `module` the
listed basename unchanged, then make 012's check an exact `==`.

`LoadOk.modules` stays lowercased. Those names come from Windows, whose
casing for system DLLs varies, and `win32.module_names` lowercases them on
purpose. Only `module`, the key into `dlls.list`, changes.

**Check on the real install (6860):** `redo` the `concommands` atoms and
`data/dlls/concommands.tsv`, and report what changed. Every DLL with a queue
may already be lowercase on disk. In that case the documents and the TSV are
byte-identical, and the report should say so.

**Scope:** `src/dllscan/facets.py`, `src/dllscan/facets_test.py`,
`src/deadlock/dlls_concommands.py`, `src/deadlock/dlls_concommands_test.py`.
A sibling (013) is editing `src/dllscan/reglist.py` concurrently; don't touch
it. Run the real check after 013 lands if its `redo` would collide with
yours; `status:` in 013's handoff file shows whether it has landed.

## Steps

- [x] Red: `facets_test` expects `Server.DLL` kept; `dlls_concommands_test`
      rejects `{"Server.dll": SERVER}` (module `server.dll`). Both failed as expected
- [x] Green: `facets.concommands` drops `.lower()`; `table` asserts `==`
- [x] Real check (6860), after 013 landed: `redo-ifchange
      data/dlls/concommands.tsv`; diffed against `trash/014-before/` (pre-013, pre-014)

## Decisions

- Test DLL path stays `...\\BIN\\Server.DLL`: a mixed-case basename is what
  proves "unchanged". `QT` fixture is now `Qt5Core.dll`, as listed.

## Open Questions

- None. 012's Open Question on `module` is settled (assert is now `==`).

## Final report

Files: `src/dllscan/facets.py`, `src/dllscan/facets_test.py`,
`src/deadlock/dlls_concommands.py`, `src/deadlock/dlls_concommands_test.py`.

API: `dllscan.facets.concommands(mem, image, dll: str) -> ConCommandsDocument`,
`module` = `ntpath.basename(dll)`, case kept (was `.lower()`).
`deadlock.dlls_concommands.table(documents)` asserts
`d["module"] == dll` for each key. `LoadOk.modules` stays lowercased.

Real run, 6860, against the snapshot `trash/014-before/` (taken before both 013
and 014):
- 014: five documents change in `module` only, all with empty queues:
  `qt5concurrent.dll` → `Qt5Concurrent.dll`, likewise `Qt5Core`, `Qt5Gui`,
  `Qt5Widgets` and `SDL3`. These are the only mixed-case basenames in `dlls.list`,
  and none has a command queue, so 014 changes no TSV row.
- 013: `rendersystemdx11.dll.json` goes from `[]` to 7 commands (`r_dx11_report_live_objects`
  … `r_textures_evict_all`). Those are the TSV's only change: 1411 → 1418 rows,
  7 added lines.

Checks: both new assertions observed red, then green; `pytest src/dllscan` +
`dlls_concommands_test` pass; `pyright` on the four files 0 errors.
Deviations: none.
