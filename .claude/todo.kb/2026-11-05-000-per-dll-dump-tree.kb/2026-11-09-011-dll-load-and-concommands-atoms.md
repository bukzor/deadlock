---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-09-010-dll-file-facet.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-008-dllscan-main-load-concommands-strides.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-009-dll-inventory-and-dlls-list.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-010-dll-file-facet.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/cvar-dump.kb/dll-coverage.md
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

- [x] Tests against a stub: 15 red (the 16th, vacuous on `{}`, red under a mutant)
- [x] `dll_load.py` green; 13 hand mutants (`trash/dll-load-mutants/run.py`) killed
- [x] `load` and `concommands` `.do` files; smoke: ok / failed / excluded
      records; `concommands` refuses `failed`, `excluded`, unlisted
- [x] Real run (6860), drivers + logs in `trash/dll-load-run/`

## Decisions

- **Two CLI subcommands, no shell logic on JSON.** `excluded NAME` prints
  the record or nothing, so the `.do` writes it to `$3` and runs the scanner
  only if `$3` is empty (no control flow on an exit status). `ok PATH`
  asserts; its `AssertionError: ('load outcome', 'failed')` names the
  outcome, and redo names the target.
- **No `facets.dumps` import**, as in 010: an excluded DLL's atom never runs
  the scanner, so must not depend on it. A test holds the output equal.
- **One reason string for all four**, with its build: the cause is shared and
  `load.tsv` shows it per row. Keys are exact `dlls.list` basenames (all
  lowercase on 6860), no case folding.
- **Deps are branch-local:** the guard's modules first, then (excluded) none
  more, or (loaded) the DLL, `bin/winpy`, and `src/dllscan/*.py` minus
  `*_test.py`. An excluded atom doesn't re-run on scanner edits.
- **Timeout left at 60 s:** `nvngx_dlss` concommands is 9.8 s end to end.
- **The winpy argv block is duplicated** in both `.do` files (8 lines): a
  helper is out of scope; extract one when `convars` makes it three.

## Open Questions

- [ ] A `load` (and `concommands`) document depends on the DLL's import
      closure, not only its own file. Declared deps miss a patch that changes
      only an imported DLL's import table. Cheap fix: after the load,
      `redo-ifchange` the `modules` that are in `dlls.list` (case-folded).
- [ ] `shellcheck` isn't installed here: the `.do` files are unchecked.

## Final report

Files (new): `src/deadlock/dll_load.py` (+ test), `data/dlls/{load,concommands}/default.json.do`.

API, `deadlock.dll_load`:
- `EXCLUDED: Mapping[str, str]`: `assetpreview.dll`, `helpsystem.dll`,
  `propertyeditor.dll`, `toolframework2.dll` → `"LoadLibrary hangs and
  leaves an unkillable process (build 6851)"`.
- `excluded(basename: str) -> LoadExcluded | None`;
  `require_ok(document: object) -> None` (`AssertionError` naming the outcome).
- CLI: `python -m deadlock.dll_load excluded NAME` (record or nothing);
  `python -m deadlock.dll_load ok PATH` (exit 0, or 1 naming the outcome).
  A later load-time facet's `.do` copies `concommands/default.json.do`.

Real run (6860, 97 DLLs, `redo -j8`):
- `load`: 91 ok, 2 failed (`phonon4`, `vfx_dx11`: `LoadLibraryExW: 126`),
  4 excluded. 17.5 s wall, no timeouts.
- `concommands` over the 91 ok: 1411 commands (= 007 strict), 29 DLLs with
  a queue (server 493, client 428, engine2 220, soundsystem 97, tier0 24, …).
  20.6 s wall. Guard: `failed`, `excluded`, unlisted each exit 1, no target.
- Second `redo-ifchange` of all 188: runs nothing, 0.7 s.
- Forced `redo -j8` of all 188: 37 s, every document byte-identical (sha256).

Checks: pytest 16 passed; pyright 0 errors; 13 mutants killed. Deviations:
none from the brief.
