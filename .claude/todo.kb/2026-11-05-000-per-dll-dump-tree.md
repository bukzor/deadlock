---
managed-by: Skill(llm-subtask)
status: open
---

# Per-DLL data store: `dlls.list` → `dlls/<facet>/<dll>.json` → `dlls/<facet>.tsv`

**Priority:** next up
**Complexity:** medium-high: a Windows-side ctypes scanner driven from WSL redo, plus WSL aggregates
**Context:** `docs/dev/convar-dump.kb/` (read all of it; `output-views.md` is the agreed layout)

## Problem Statement

Build a store of data about the game DLLs: lossless per facet, not
tuned to one purpose, so next week's question about DLLs finds it still valid.
Purposes are filters and views over the store. The first purpose: every convar
and concommand declaration, offline, deterministic, duplicates kept, with
committed TSVs for `git diff` across patches.

## Current Situation

Prototyped, not built. The prototypes are archived in `docs/dev/probes/`
(Windows Python, run from WSL; see "Running the probes" below):

- `convar_scan.py` + `fixed_stride_scan.py` + `run_all.py`: the shape scan
  (`capture-approach.kb/queue-shape-scan.md`), the leading approach. Finds both
  queues per DLL; names, help, flags decode. **Value fields (type, default,
  min, max) in the queue are not decoded yet.**
- `hook_probe2.py`, `hook_probe3.py`: the `ICvar` hook, placeholder factory,
  controlled `Init`, and tier0 registry readback
  (`capture-approach.kb/icvar-hook.md`). Not a producer of the dump: the
  validator for value decoding and, later, for the merged view.
- Results on 6854 `server.dll`: queue 2008 convars / 493 commands, all of them
  registered; registry by access index 2003 names; 1991 of 2002 registry
  defaults equal GameTracking-Deadlock's `DumpSource2/convars.txt` for 6854
  (the 11 others are engine2/client-owned names reading zero).
- The install is 6860: 97 DLLs (645 MB), all under `game/bin/win64` (incl.
  `qt5_plugins/`, `subtools/`) and `game/citadel/bin/win64`; basenames
  unique; 47 import tier0. The queue numbers above are older, so re-check them.
- Measured 2026-11-08 (6860; `docs/dev/probes/load_time.py`, `pe_size.py`):
  `python.exe -c pass` from WSL 73-123 ms; `LoadLibrary` ≤ 40 ms
  (`client.dll`), ~0.2 s per Windows process end to end; WSL `import pefile`
  0.2 s. `pefile`'s dump of all 97 is 149 MB, 14 MB of it
  without the base-relocation list (`server.dll` 83 KB; `v8.dll` 1.6 MB, its
  16384 exports).

## Design

**Atomic production.** One process per (facet, DLL): its own redo target, its
own deps, so a change to one facet's code re-runs only that facet, and
`redo -j` parallelises everything. ~0.2 s overhead per atom makes this cheap;
measure the first full build to confirm. Facets that would share an expensive
acquisition share an atom instead (see Open Questions).

**Lossless per facet.** Each facet dumps everything its source exposes, not
hand-picked fields; bulk that is pure noise becomes a count and a hash, by a
stated rule. A purpose (which DLLs carry convar queues, a server-only view) is
a filter over the store, never a filter baked into it.

**Tree, facet-first under one root:**

| path | committed | what |
|---|---|---|
| `data/dlls.list` | no | membership only: every `*.dll` under `game/`, paths relative to `game/`, sorted; basenames asserted unique. Changes only when a DLL is added, removed or renamed, so it never re-runs the atoms on a patch |
| `data/dlls/<facet>/default.json.do` | `.do` yes | one per facet; `$2` = DLL basename; guard: basename in `dlls.list` (load-time facets: and `load/<dll>.json` says `ok`), else fail |
| `data/dlls/<facet>/<dll>.json` | no | one document: one facet, one DLL |
| `data/dlls/default.tsv.do` | yes | case table on `$2` = facet; one `redo-ifchange` over that facet's documents, then `deadlock.dlls_<facet>` |
| `data/dlls/<facet>.tsv` | per facet | the facet's lossless aggregate, one row per item |
| `data/dlls.check/strides` | no | re-learns the strides from `server.dll`, non-zero if they moved; in `all.do` |

A per-DLL overview (`data/dlls.tsv`, one row per DLL joining scalars across
facets) is a later view, built when a question needs it.

### Facets

| facet | side | content |
|---|---|---|
| `file` | WSL | size, sha256 |
| `load` | Windows | outcome: `ok` (+ the modules the load pulled in, sorted), `failed` (+ the error), or `excluded` (+ the reason; never loaded, written WSL-side). A timeout fails the build: a hung load can leave an unkillable process, so the fix is a new exclusion |
| `convars` | Windows | the convar reg-list queue: `{module, convars: [...]}`, entries in queue order |
| `concommands` | Windows | the same for the command queue |
| `pe` (later) | WSL | static PE metadata: headers, sections (+ sha256 each), imports, exports, debug/CodeView, rich header, version and other resources, load config, TLS; relocations and `.pdata` as count + hash |
| `interfaces` (later) | Windows | the `InterfaceReg` list, filled at static init like the queues |
| `registry` (later, on demand) | Windows | `Init`-time registry readback via the `ICvar` hook; a check, never a source |

Every load-time facet runs on every DLL whose load is `ok`, not only tier0
importers: "only tier0 importers carry queues" becomes a fact checked against
the store.

### `src/dllscan/`: the scanner (Windows side, stdlib only)

It is a top-level package of its own, not `deadlock.*`, so the stdlib-only
rule has a boundary that a test can enforce. Every module except `win32` is
pure: it reads memory through a `read(addr, n) -> bytes | None` callable, so
WSL pytest drives it with a fake. It must be 3.12-compatible (WSL pins 3.12).

| module | what it owns |
|---|---|
| `memory` | `Memory` over a `read` callable: `u32`, `u64`, `cstr_in(addr, lo, hi)` (NUL-terminated printable, inside a range); `Segments`, a `{base: bytes}` fake for tests |
| `image` | a loaded PE image's layout read through `Memory`: image range, writable sections |
| `reglist` | the reg-list queue: `walk(mem, head, stride, image)` → entry addresses in replay order (or `None` on misfit); `find_heads(mem, image, stride)` over writable sections with the owner check; `learn_strides` (pass 1); `STRIDES = {convars: 160, concommands: 64}` pinned |
| `flags` | FCVAR bit → name (s2sdk `convar.h`, lowercased, unprefixed, DumpSource2 spelling), unknown bits → `flag_<n>` |
| `values` | the binary's `EConVarType` table; decodes `CVValue_t` bytes by type to a JSON value, anything undecodable to hex |
| `entries` | `decode_convar(mem, addr, image)` / `decode_concommand(…)`: creation-struct offsets → `{name, help, flags, type, default, min, max}` / `{name, help, flags}` (queue index is list position, never a field); every shape check from `validation.md` raises `ShapeError` |
| `document` | the `TypedDict`s of every facet's document; `deadlock` imports them, so pyright checks both sides of the process boundary |
| `win32` | the only Windows-only module (ctypes): `add_dll_directory` both bin dirs and the DLL's own, `LoadLibraryExW` → base, loaded-module list, `ReadProcessMemory` as the `read` callable, `hard_exit(code)`: flush stdout, then `TerminateProcess` (skips DLL detach / static destructors) |
| `__main__` | CLI, one subcommand per load-time facet: `load DLL`, `convars DLL`, `concommands DLL` print that facet's document; `strides DLL` learns and compares to the pinned values. Any exception → message on stderr, `hard_exit(1)` |
| `registry` (later) | from `hook_probe3.py`: ICvar hook, placeholder factory, registry readback |

There is also `stdlib_only_test.py`, which parses every module with `ast` and
fails on any import outside `sys.stdlib_module_names` and `dllscan`.

No document has a `build` field: the DLL's bytes already key the target,
so a build stamp would only add churn.

### `bin/winpy`: the process boundary (bash, ≤50 lines)

`bin/winpy MODULE ARGS…` runs `python.exe -m MODULE` with `src/` on
`PYTHONPATH` (Windows path, passed via `WSLENV`) and stdin from `/dev/null`
(`python.exe` reads its inherited stdin; under redo it would eat the caller's).
Its cwd is a scratch dir, `trash/winpy/`, which catches `*.mdmp` files. It
runs under `timeout` and passes the exit status through. If `python.exe` is
missing it fails loudly. That is the whole host policy: `all.do` always builds
the DLL facets, never skips them.

### `src/deadlock/` additions (WSL side, tests beside)

| module | what it owns |
|---|---|
| `paths` | add `bin_dirs` (`game/bin/win64`, `game/citadel/bin/win64`), passed to `dllscan` |
| `dll_inventory` | prints `dlls.list`: every `*.dll` under `game/`, sorted, basenames asserted unique |
| `dll_file` | the `file` facet |
| `dll_load` | `EXCLUDED: dict[basename, reason]`, the `excluded` record; `helpsystem`, `assetpreview`, `propertyeditor`, `toolframework2` hang in `LoadLibrary` (unkillable process, 6851) |
| `dlls_<facet>` | one aggregator per facet: that facet's documents → `<facet>.tsv`, sorted, cells escaped; `convars`/`concommands` keep queue order within a module (test: row ordinal = list position) |
| `registry_check` (later) | `registry` vs `convars`: every once-declared name's type, flags minus the per-DLL flag, and default |

## Implementation Steps

The scanner core comes first: the value-field fit reads entries through
`memory`/`image`/`reglist`/`win32`, so it runs on the real scanner rather than
on another prototype.

- [x] Scanner core, names/help/flags only (port `convar_scan.py` /
      `fixed_stride_scan.py`, TDD against `Segments`)
  One sub-agent per item, coordinated from the main session; waves run in
  parallel, each wave after the one it depends on. Each agent's brief and
  report is a file in `2026-11-05-000-per-dll-dump-tree.kb/` (protocol in
  its `CLAUDE.md`).
  - [x] Wave 1: package skeleton (`pyproject.toml` hatch packages,
        `__init__`, `stdlib_only_test.py`) + `dllscan.memory`
        (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-001-dllscan-skeleton-and-memory.md>)
  - [x] Wave 1: `dllscan.flags`
        (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-002-dllscan-flags-table.md>)
  - [x] Wave 1: `dllscan.document`
        (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-000-dllscan-document-types.md>)
  - [x] Wave 2 (after memory): `dllscan.image`
        (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-003-dllscan-image-layout.md>)
  - [x] Wave 3 (after image): `dllscan.reglist`
        (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-004-dllscan-reglist.md>)
  - [x] Wave 3 (after memory, beside `reglist`): `dllscan.win32`, `bin/winpy`.
        Verify Windows Python takes a `\\wsl.localhost\…` entry on `PYTHONPATH`
        (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-005-dllscan-win32-and-winpy.md>)
  - [x] Wave 4 (after `reglist`): `dllscan.entries`, names/help/flags only
        (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-006-dllscan-entries-names-help-flags.md>)
  - [x] Wave 5 (after `entries`): `dllscan.__main__ load|concommands|strides`
        (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-008-dllscan-main-load-concommands-strides.md>)
        (`convars` waits for the value decode: no placeholder values), and on
        the real install: time `find_queues` on `server.dll` and settle the
        `reglists` question below; re-run 6860 `server`/`client` queue counts
        against the 6854 ones
- [x] Settle the `rendersystemdx11` owner-check exception: a per-kind ref
      check (commands: the ref reads u16 `0xFFFF`; convars: the owner check)
      (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-013-reglist-per-kind-ref-check.md>)
  - [x] Evidence (6860): <https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-007-rendersystemdx11-owner-check-evidence.md>
- [ ] Decode the value fields against the engine (`dllscan.values`, `dllscan.entries`)
  - [~] Fit the layout (research): <https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-018-convar-value-layout-fit.md>
  - [ ] Find `ConVarValueInfo_t`'s offsets inside the 160-byte entry (s2sdk
        `convar.h:630-730`: version, has-default/min/max, three `CVValue_t`,
        callbacks, `m_eVarType`; s2sdk's copy is stale on the type enum, so
        expect drift). Fit them with `hook_probe3.py`'s readback: for names
        declared once, the entry must contain the registry's type code and
        default bytes
  - [ ] Use the binary's `EConVarType`: `bool int8 uint8 int16 uint16 int32
        uint32 int64 uint64 float32 float64 string color vector2 vector3
        vector4 qangle vectorws` (`registration-flow.md`)
  - [ ] Decode the 64-byte command entry beyond name/help/flags only if it
        holds something worth dumping (callback is a pointer: drop it)
  - [ ] Pass: every once-declared `server` and `client` convar's type, default,
        min, max equal the registry's; record the layout in
        `registration-flow.md` with the build
- [x] `dllscan.__main__ strides`; all `validation.md` shape checks raise
- [x] `deadlock.paths.bin_dirs`, `deadlock.dll_inventory`, `data/dlls.list.do`
      (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-009-dll-inventory-and-dlls-list.md>)
- [x] `deadlock.dll_file`, `data/dlls/file/default.json.do`
      (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-010-dll-file-facet.md>)
- [x] `deadlock.dll_load`, `data/dlls/load/default.json.do`; load all 97, add
      any new hang to `EXCLUDED` with its reason; and
      `data/dlls/concommands/default.json.do`
      (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-011-dll-load-and-concommands-atoms.md>, after 010)
- [ ] `data/dlls/convars/default.json.do` (after the value decode), with its
      check: the convar anchor (`citadel_lane_swap_available_duration_prematch`
      ⊇ `replicated cheat`) and convar coverage (`engine2`, `client`,
      `server` each yield a convar queue), as `data/dlls.check/concommands` does
- [ ] Load-time atoms depend on the DLL's import closure, not only its file:
      after the load, `redo-ifchange` the `modules` that are in `dlls.list`
- [x] `deadlock.dlls_{file,load,convars,concommands}`, `data/dlls/default.tsv.do`
      (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-012-dlls-facet-aggregates.md>: all but `convars`)
- [x] A document's `module` is the listed basename, case kept
      (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-014-module-is-the-listed-basename.md>)
- [x] `reglist.find_queues(mem, image, kind)` instead of a stride, and
      `reglist_test.py` under 300 lines (move `Fake` to `reglist_fake.py`)
      (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-017-find-queues-by-kind-and-reglist-fake.md>)
- [x] Commit the tree's prior uncommitted work
      (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-015-commit-prior-uncommitted-work.md>)
- [x] `data/dlls.check/strides.do`; checks `validation.md` lists but no target
      owns yet: the anchors (they also label the strides) and coverage
      (`engine2`, `client`, `server` each yield both queues)
- [x] Wire up (<https:2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-016-wire-the-store-into-the-build.md>, with the strides step above): `.gitignore` (ignore `data/dlls/*/`, keep `data/dlls/*.tsv`
      and every `*.do`); add the committed aggregates to `all.do`'s
      `committed` list (`redo-adopt`) and the strides check to its deps;
      README views table
- [ ] On-demand checks: `dllscan.registry` + `deadlock.registry_check` for
      `server`/`client`; the `cvarlist` oracle (`capture-approach.kb/runtime-cvarlist.md`)
- [ ] Docs: drop each `[!TODO]` callout as it lands; record the tool choice in
      `docs/dev/decisions.kb/` (it departs from `reuse-existing-parsers.md`,
      `convar-dump.kb/CLAUDE.md` says why that matters), and the lossless
      store + atomic facets as a decision of its own; rewrite
      `capture-approach.md` as the answer once its `[!QUESTION]` closes
- [ ] Commit (`Command(commit)`)

## Open Questions

- `convars` and `concommands` as two facets, or one `reglists` facet: two
  atoms scan the same writable sections twice. Merge if `find_heads` on
  `server.dll` turns out slow.
- The engine's merged view (later, separate): the merge rule, the 5
  unexplained flag changes, the 11 zero defaults, whether tier0's own queue
  (`find`, `cvarlist`) registers only in tier0's `Init`, its scope (all DLLs
  is the default). All in `output-views.md` / `icvar-hook.md` `[!QUESTION]`s.

## Success Criteria

- [ ] From clean, `redo -j8 data/dlls/convars.tsv data/dlls/concommands.tsv`
      builds every atom in parallel and exits 0
- [ ] Every DLL in `dlls.list` has a `load` record; every `ok` one has a
      `convars` and a `concommands` document
- [ ] Row counts equal the queue counts, duplicates kept (6854 `server`: 2008
      convars, 493 commands)
- [ ] Two consecutive builds are byte-identical
- [ ] Registry readback check passes for `server` and `client`
- [ ] `./bin/shell pytest`, `./bin/shell pyright` clean

## Notes

Running the probes, from the repo root: `mkdir -p trash/hook && cd
trash/hook && python.exe "$(wslpath -w ../../docs/dev/probes/hook_probe3.py)"
server.dll Source2ServerConfig001 </dev/null`. The probes hardcode the stock
`C:\Program Files (x86)\Steam` install; the real scanner takes the DLL path
as an argument, which the `.do` derives from `DEADLOCK_HOME` (`python -m
deadlock.paths game_dir`, `wslpath -w`). `python.exe` (Windows 3.14) is on the WSL `PATH` and
accepts a `\\wsl.localhost\…` script path; run from a scratch dir.
Disassembly and PE parsing in WSL without touching the project deps:
`uv run -q --no-project --with capstone --with pefile python …`; helpers in
`docs/dev/probes/` (`disas.py`, `xref_global.py`, `mdmp_exc.py`).

The game install is unusable while Steam updates it (`citadel/bin/win64/`
empties). Numbers in the KB are labelled by build.
