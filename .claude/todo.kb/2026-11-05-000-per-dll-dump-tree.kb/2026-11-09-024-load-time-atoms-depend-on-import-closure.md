---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-09-023-one-winpy-facet-invocation.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-011-dll-load-and-concommands-atoms.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-014-module-is-the-listed-basename.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-023-one-winpy-facet-invocation.md
  - ~/.claude/must-read.kb/before/writing-bash-scripts.md
---

# Load-time atoms depend on the DLL's import closure

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the step "Load-time
atoms … depend on the DLL's import closure")

## Problem Statement

The `load`, `concommands` and `convars` atoms load the DLL in a Windows
process, so their output depends on every DLL that load pulls in, not only on
the DLL's own file. Today they `redo-ifchange` only the DLL's file. A patch
that changes `tier0.dll` alone leaves `server.dll`'s atoms stale.

The closure is known after the load: an `ok` load document's `modules` lists
the modules the load added. After an atom runs, it declares
`redo-ifchange` on the files of those modules that are in `data/dlls.list`. A
dependency declared after the build is normal in redo. Modules outside the
list (system DLLs) stay untracked. `modules` holds the loader's names and
`dlls.list` keeps the files' case, so the match ignores case (014). Put the
mapping in a small `deadlock` module, not in bash. Keep excluded and `failed`
atoms as they are: an excluded atom still depends on no scanner and no DLL.

How do `concommands` and `convars` learn the closure: from their own output,
or from the `load` document? Settle it, keeping each atom's dependencies
exact, and report it.

**Acceptance (6860):**
- `redo` at the repo root exits 0, `git diff data/` is empty, and every atom
  document is byte-identical to a snapshot taken before the change.
- A second `redo` runs nothing.
- `redo-sources` for `server.dll`'s three atoms now include `tier0.dll`'s file;
  an excluded DLL's `load` atom lists the same sources as before. Show the
  before and after.
- `touch` on `tier0.dll`'s file, then `redo`, rebuilds `server.dll`'s atoms.
  It is the game install's file: save its mtime first (`touch -r` to a file
  in `trash/`), restore it afterwards, and `redo` once more so the tree
  settles.

**Scope:** `data/dlls/{load,concommands,convars}/default.json.do`, `bin/winpy-facet.bash` (023), and a new `src/deadlock/` module with its test.

## Steps

- [x] Baseline: `redo` ran nothing; snapshot `trash/024/data.before.sha256` (606 files), deps
      `trash/024/deps.before` (query: `trash/024/deps.sh`)
- [x] `deadlock.dll_closure` + test: 5 red on a stub, 7 green; 7 hand mutants
      (`trash/024/mutants.py`) killed, covering the 2 tests vacuous on the stub
- [x] `closure` step in `bin/winpy-facet.bash`; the three `.do`s call it; `shellcheck` clean
- [x] Acceptance run (6860), logs `trash/024/redo*.log`

## Decisions

- **`concommands`/`convars` read the closure from the `load` document.** Their own output
  names no modules, and they already depend on that document (`require_loaded`). It is the
  same load: `dllscan` loads the DLL with the same `LoadLibraryExW`, flags and search dirs in
  a fresh process. The closure is declared *before* their scan runs. The `load` document's
  `redo-stamp` would hide a `tier0.dll` change that leaves `modules` unchanged, so each atom
  declares the files itself. Depending on the document alone would not be enough.
- **`load` runs `closure "$3"` after its scan**, inside the not-excluded branch: an
  excluded atom's sources are unchanged. A `failed` document maps to no DLLs (the load stopped
  before saying what it added). The `failed` atom does gain `dll_closure.py`, since it runs
  that module. An `excluded` document passed to `closure` is an `AssertionError`.
- **NUL-delimited `xargs -r0`** (via `tr`): `/usr/bin/xargs` is BusyBox, which has no `-d`,
  and the install path has spaces.
- The DLL itself is in its own `modules`, so it is declared twice. redo doesn't mind.

## Open Questions

- [ ] drvfs (`/mnt/c`) keeps mtimes to the second only when set: tier0.dll's
      `20:28:53.2332304` came back as `20:28:53.0` (`touch -r`, `touch -d`, `os.utime(ns=)`
      all truncate). Its content is untouched.

## Final report

Files: new `src/deadlock/dll_closure.py` (+ `_test.py`); `bin/winpy-facet.bash` (+`closure`,
now 50 lines); `data/dlls/{load,concommands,convars}/default.json.do` (+1 line each).

API:
- `deadlock.dll_closure.closure(listing: Iterable[str], document: object) -> list[str]`:
  the `dlls.list` entries whose basename matches a `modules` name, ignoring case, in listing
  order. `[]` for `failed`, `AssertionError` for anything else.
- CLI `python -m deadlock.dll_closure LOAD.json <data/dlls.list`: each such DLL's path under
  `game/`, one per line.
- `bin/winpy-facet.bash`: `closure LOAD`: `redo-ifchange` on `dll_closure.py` and those paths.
  A new load-time facet's `.do` is `lookup; require_loaded; closure "../load/$2.json"; dllscan`.

Acceptance (6860):
- `redo -j8` at the root: exit 0, 98 s; all 606 files under `data/` (minus `*.do`) match the
  snapshot (sha256). `git diff data/` is only the three `.do` sources (+1 line each).
- Second `redo`: only `all`, `(data/gamedata.list)`, `data/date.txt` (always-run).
- Deps (`trash/024/deps.{before,after}`): `{load,concommands,convars}/server.dll` each gain
  `game/bin/win64/{steam_api64,tier0}.dll` and `src/deadlock/dll_closure.py`.
  `load/helpsystem` (excluded) is unchanged. `load/phonon4` (failed) gains `dll_closure.py` only.
- `touch` tier0.dll then `redo -j8`: 129 load-time atoms rebuilt, including all three of
  `server.dll`'s. Mtime restored (see Open Questions), `redo` again, then a third `redo` runs
  nothing and the data matches the snapshot.

Checks: pytest (dll_closure, dll_load, dlls_list) 29 passed; pyright 0 errors on the new files.
Deviation: the `failed` atom's extra `dll_closure.py` dependency (above).
