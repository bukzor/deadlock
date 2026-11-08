---
managed-by: Skill(llm-subtask)
status: active
---

# Per-DLL dump tree: `dlls.list` → `dlls.json/` → `dlls.tsv/`

**Priority:** next up
**Complexity:** medium-high: a Windows-side ctypes scanner driven from WSL redo, plus two WSL views
**Context:** `docs/dev/convar-dump.kb/` (read all of it; `output-views.md` is the agreed layout)

## Problem Statement

Dump every convar and concommand declaration out of the game DLLs, offline,
deterministically, losslessly (duplicates kept), one independent target per
DLL so `redo -j` parallelises, and commit TSV views for `git diff` across
patches. The per-DLL JSON is meant to grow more sections later (interfaces,
logging channels, schemas).

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
- The install is 6857 (Nov 05 12:51); the numbers above are from older
  builds, so re-check them first.

## Components

Two packages split along the process boundary. Windows Python 3.14 runs with
no venv and loads the DLLs; WSL owns everything after its stdout.

### `src/dllscan/`: the scanner (Windows side, stdlib only)

It is a top-level package of its own, not `deadlock.*`, so the stdlib-only
rule has a boundary that a test can enforce. Every module except `win32` is
pure: it reads memory through a `read(addr, n) -> bytes | None` callable, so
WSL pytest drives it with a fake. It must be 3.12-compatible (WSL pins 3.12).

| module | what it owns |
|---|---|
| `memory` | `Memory` over a `read` callable: `u32`, `u64`, `cstr_in(addr, image)` (NUL-terminated printable, inside a range); `Segments`, a `{base: bytes}` fake for tests |
| `image` | a loaded PE image's layout read through `Memory`: image range, writable sections |
| `reglist` | the reg-list queue: `walk(mem, head, stride, image)` → entry addresses in replay order (or `None` on misfit); `find_heads(mem, image, stride)` over writable sections with the owner check; `learn_strides` (pass 1); `STRIDES = {convars: 160, concommands: 64}` pinned |
| `flags` | FCVAR bit → name (s2sdk `convar.h`, lowercased, unprefixed, DumpSource2 spelling), unknown bits → `flag_<n>` |
| `values` | the binary's `EConVarType` table; decodes `CVValue_t` bytes by type to a JSON value, anything undecodable to hex |
| `entries` | `decode_convar(mem, addr, image)` / `decode_concommand(…)`: creation-struct offsets → `{index, name, help, flags, type, default, min, max}` / `{index, name, help, flags}`; every shape check from `validation.md` raises `ShapeError` |
| `scan` | one DLL → its document `{module, convars: [...], concommands: [...]}`: at most one head per kind, decode every entry, no addresses |
| `win32` | the only Windows-only module (ctypes): `add_dll_directory` both bin dirs, `LoadLibraryExW` → base, `ReadProcessMemory` as the `read` callable, `hard_exit(code)` via `TerminateProcess` (skips DLL detach / static destructors) |
| `__main__` | CLI. `scan DLL`: JSON on stdout. `strides DLL`: learn and compare to the pinned values. Any exception → message on stderr, `hard_exit(1)` |
| `registry` (later) | from `hook_probe3.py`: ICvar hook, placeholder factory, registry readback. Subcommand `registry DLL IFACE` → JSON. It is an on-demand check, never the dump's source |

There is also `stdlib_only_test.py`, which parses every module with `ast` and
fails on any import outside `sys.stdlib_module_names` and `dllscan`.

The document has no `build` field: the DLL's bytes already key the target,
so a build stamp would only add churn.

### `bin/winpy`: the process boundary (bash, ≤50 lines)

`bin/winpy MODULE ARGS…` runs `python.exe -m MODULE` with `src/` on
`PYTHONPATH` (Windows path, passed via `WSLENV`). Its cwd is a scratch dir,
`trash/winpy/`, which catches `*.mdmp` files. It runs under `timeout` and
passes the exit status through. If `python.exe` is missing it fails loudly.
That is the whole host policy: `all.do` always builds the DLL views, never skips them.

### `src/deadlock/` additions (WSL side, tests beside)

| module | what it owns |
|---|---|
| `paths` | add a `bin_dirs` resolver (`game/bin/win64`, `game/citadel/bin/win64`) |
| `dll_scope` | `in_scope(imports_by_dll)`: every DLL importing `tier0.dll`, plus tier0, minus `EXCLUDED: dict[name, reason]`. The CLI prints `dlls.list` (paths relative to `game/`, sorted) and asserts basenames are unique. PE imports via `pefile` (`uv add`) |
| `dll_dump` | typed loading of `dlls.json/*.json` documents and TSV cell rendering, shared by the views |
| `convars` | view: JSON paths → TSV `name module index type default min max flags help`, sorted by (name, module, index) |
| `concommands` | view: the same for `name module index flags help` |
| `registry_check` (later) | `dllscan registry` output vs the dump: every once-declared name's type, flags minus the per-DLL flag, and default |

### redo targets

| target | committed | built from |
|---|---|---|
| `data/dlls.list` | no | `deadlock.dll_scope`; depends on `dll_scope.py`, `paths.py`, `deadlock-version.json`; `redo-stamp` |
| `data/dlls.json/<dll>.json` | no | guard: basename in `dlls.list`, else fail. `bin/winpy dllscan scan <winpath>`; depends on `src/dllscan/*.py`, `bin/winpy`, the DLL file; `redo-stamp` |
| `data/dlls.tsv/{convars,concommands}.tsv` | yes | case table; one `redo-ifchange` over every `dlls.json/<dll>.json`, then `deadlock.<view>` |
| `data/dlls.check/strides` | no | `bin/winpy dllscan strides server.dll`; non-zero if the strides moved. In `all.do` |
| `data/dlls.check/registry/<dll>` (later) | no | `dllscan registry` → `deadlock.registry_check`; on demand, for `server` and `client` |

## Implementation Steps

The scanner core comes first: the value-field fit reads entries through
`memory`/`image`/`reglist`/`win32`, so it runs on the real scanner rather than
on another prototype.

- [ ] Scanner core, names/help/flags only (port `convar_scan.py` /
      `fixed_stride_scan.py`, TDD against `Segments`)
  - [ ] `pyproject.toml`: add `src/dllscan` to the hatch packages
  - [ ] `dllscan.memory`, `dllscan.image`, `dllscan.reglist`, `dllscan.flags`, `stdlib_only_test.py`
  - [ ] `dllscan.win32`, `dllscan.__main__ scan`; `bin/winpy`. Verify Windows
        Python takes a `\\wsl.localhost\…` entry on `PYTHONPATH`
  - [ ] Re-run on 6857: `server`/`client` counts against the 6854 ones
- [ ] Settle the `rendersystemdx11` owner-check exception (6 of 7 entries pass,
      6851; `queue-shape-scan.md` `[!QUESTION]`): read the odd entry, decide
      whether a null or out-of-image ref is legal, then make the check strict
- [ ] Decode the value fields against the engine (`dllscan.values`, `dllscan.entries`)
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
- [ ] `dllscan.scan` + `dllscan.__main__ strides`; all `validation.md` shape checks raise
- [ ] `deadlock.paths.bin_dirs`, `deadlock.dll_scope` (`uv add pefile`), `data/dlls.list.do`
      (46 on 6851). Exclusions, each with its reason: `helpsystem`,
      `assetpreview`, `propertyeditor`, `toolframework2` hang in `LoadLibrary`
      (unkillable process), `vfx_dx11` fails to load
- [ ] `data/dlls.json/default.json.do`
- [ ] `deadlock.dll_dump`, `deadlock.convars`, `deadlock.concommands`, `data/dlls.tsv/default.tsv.do`
- [ ] `data/dlls.check/strides.do`
- [ ] Wire up: `.gitignore` exceptions for `data/dlls.tsv/*.tsv` and the
      `*.do` files (pattern as `gamedata.tsv`); add both views to `all.do`'s
      `committed` list (`redo-adopt`) and the strides check to its deps; README views table
- [ ] On-demand checks: `dllscan.registry` + `deadlock.registry_check` for
      `server`/`client`; the `cvarlist` oracle (`capture-approach.kb/runtime-cvarlist.md`)
- [ ] Docs: drop each `[!TODO]` callout as it lands; record the tool choice in
      `docs/dev/decisions.kb/` (it departs from `reuse-existing-parsers.md`,
      `convar-dump.kb/CLAUDE.md` says why that matters); rewrite
      `capture-approach.md` as the answer once its `[!QUESTION]` closes
- [ ] Commit (`Command(commit)`)

## Open Questions

- The engine's merged view (later, separate): the merge rule, the 5
  unexplained flag changes, the 11 zero defaults, whether tier0's own queue
  (`find`, `cvarlist`) registers only in tier0's `Init`, its scope (all DLLs
  is the default). All in `output-views.md` / `icvar-hook.md` `[!QUESTION]`s.
- Loading a listed DLL also loads its imports; if one of those is an excluded
  DLL, it hangs anyway. Check `dlls.list`'s import closure against `EXCLUDED`
  in `dll_scope`, if any listed DLL turns out to import one.

## Success Criteria

- [ ] From clean, `redo -j8 data/dlls.tsv/convars.tsv data/dlls.tsv/concommands.tsv`
      scans every listed DLL in parallel and exits 0
- [ ] Row counts equal the queue counts, duplicates kept (6854 `server`: 2008
      convars, 493 commands)
- [ ] Two consecutive builds are byte-identical
- [ ] Registry readback check passes for `server` and `client`
- [ ] `./bin/shell pytest`, `./bin/shell pyright` clean

## Notes

Running the probes, from the repo root: `mkdir -p trash/hook && cd
trash/hook && python.exe "$(wslpath -w ../../docs/dev/probes/hook_probe3.py)"
server.dll Source2ServerConfig001`. The probes hardcode the stock
`C:\Program Files (x86)\Steam` install; the real scanner takes the DLL path
as an argument, which the `.do` derives from `DEADLOCK_HOME` (`python -m
deadlock.paths`, `wslpath -w`). `python.exe` (Windows 3.14) is on the WSL `PATH` and
accepts a `\\wsl.localhost\…` script path; run from a scratch dir.
Disassembly and PE parsing in WSL without touching the project deps:
`uv run -q --no-project --with capstone --with pefile python …`; helpers in
`docs/dev/probes/` (`disas.py`, `xref_global.py`, `mdmp_exc.py`).

The game install is unusable while Steam updates it (`citadel/bin/win64/`
empties). Numbers in the KB are labelled by build.
