---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-009-dll-inventory-and-dlls-list.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-000-dllscan-document-types.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/convar-dump.kb/output-views.md
  - data/gamedata.json/default.json.do
---

# `deadlock.dll_file` and `data/dlls/file/default.json.do`

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Wave 6; row
`dll_file`, facet `file`, tree row `data/dlls/<facet>/default.json.do`)

## Problem Statement

The `file` facet: one DLL's on-disk size and sha256, as a
`dllscan.document.FileDocument`, computed WSL-side. It is the store's
cheapest atom and the template the Windows-side atoms (unit 011) follow, so
keep the `.do` shape clean and say what's reusable.

- **`data/dlls/file/default.json.do`:** `$2` is the DLL basename, e.g.
  `server.dll`.
  - Guard: the basename is a basename in `data/dlls.list` (the contract is in
    unit 009's Problem Statement; 009 is building it concurrently). If it
    isn't, fail loudly.
  - `redo-ifchange` `dlls.list`, the producing module, and the DLL file
    itself, an absolute path under the game dir. Check how
    `gamedata.json/default.json.do` depends on install files, and do the
    same.
  - Write the document to `$3`.
- **`deadlock.dll_file`:** pure function plus CLI. Output: JSON, `indent=2`,
  declared key order, trailing `\n`. That's the same formatting `dllscan`
  uses (008's Final report), so all facets diff alike.
- **Path lookup:** basename → path under `game/` via `dlls.list`. That lookup
  is needed by every atom, so write it once, in a module 011 can import (e.g.
  `deadlock.dll_inventory` owns it if 009 has landed; otherwise a small
  `deadlock.dlls_list` reader). Report where it went.

**Tests** beside the module. Then, once 009's `data/dlls.list` exists (wait
for it, or build it with `redo data/dlls.list`), run
`redo data/dlls/file/server.dll.json` for real and show the document. Also
show that an unlisted name fails.

**Scope:** `src/deadlock/dll_file.py` (+ test), the shared lookup helper
(+ test), `data/dlls/file/default.json.do`.

## Steps

- [x] Tests first (import red, stub red), then `dlls_list`, `dll_file`
- [x] 9 hand mutants (`trash/dll-file-mutants/run.sh`), all killed
- [x] `data/dlls/file/default.json.do`; pytest, pyright clean
- [x] Real install, once 009's `dlls.list.do` landed (Final report)

## Decisions

- **Lookup in `deadlock.dlls_list`, not `dll_inventory`.** 009 hadn't landed
  when this started, so the brief's fallback. It reads `dlls.list` on stdin,
  so the `.do` names the exact file it declared a dependency on.
- **The lookup CLI is the guard.** `relpath` asserts exactly one entry has
  that basename, so an unlisted name, a path, or a suffix (`ier0.dll`) fails
  with the name in the message; the `.do` needs no guard of its own.
- **`dll_file` does not import `dllscan.facets.dumps`.** `facets` imports
  the whole scanner (`win32`, `reglist`, `entries`, …): declaring those as
  deps re-runs 97 `file` atoms on every scanner edit, and not declaring them
  lies to redo. It inlines `json.dumps(doc, indent=2) + "\n"`; a test
  holds it equal to `facets.dumps`. `ensure_ascii=False` dropped: a
  size + hex document is always ASCII.
- **Output to `$3`, then `redo-stamp <"$3"`**, not the repo's
  `exec > >(tee >(redo-stamp))`: the brief says `$3`, and stamping the
  finished file has no process-substitution race. The stamp spares the
  aggregates when `dll_file.py` changes but no document does.

## Open Questions

- [ ] `dllscan.facets.dumps` belongs somewhere scanner-free (e.g.
      `dllscan.document`), so every facet can import one formatter without
      the scanner fan-in. Not in this unit's scope.

## Final report

Files (new): `src/deadlock/{dlls_list,dll_file}{,_test}.py`,
`data/dlls/file/default.json.do`.

API, for 011:
- `deadlock.dlls_list.relpath(listing: Iterable[str], basename: str) -> str`:
  the `dlls.list` line (newline stripped) whose basename is `basename`;
  `AssertionError` naming it unless exactly one matches.
- CLI, the atoms' lookup + guard in one line:
  `dll=$("$py" -m deadlock.dlls_list "$2" <"$root/data/dlls.list")` prints
  `paths.game_dir() / relpath` (absolute WSL path); a Windows atom then
  passes `"$(wslpath -w "$dll")"` to `bin/winpy`.
- `deadlock.dll_file.document(data: bytes) -> FileDocument`;
  `python -m deadlock.dll_file PATH` prints it, `json.dumps(indent=2)` + `\n`.

Reusable `.do` shape (011 copies it): `root=$(cd ../../.. && pwd)`;
`redo-ifchange` the list + the modules the CLI imports; look up (guard);
`redo-ifchange "$dll"`; produce `>"$3"`; `redo-stamp <"$3"`.

Checks: pytest 11 passed (10 tests + 1 doctest); pyright 0 errors; 9 hand
mutants all killed. Real install (6860, `dlls.list` 97 lines):
- `redo data/dlls/file/server.dll.json` → `{"size": 64616088, "sha256":
  "1415c83d…81cfd3b"}`, equal to `stat` and `sha256sum`.
- Nested `qwindows.dll` builds (sibling `qwindowsvistastyle.dll` no clash).
- `redo data/dlls/file/bogus.dll.json` → exit 1, `AssertionError:
  ('bogus.dll', 'not exactly once in dlls.list', [])`, no target written.
- Rebuild is a no-op; `redo-sources` lists the DLL's absolute path.

Deviations: lookup in `dlls_list`; no `facets.dumps` import (Decisions).
