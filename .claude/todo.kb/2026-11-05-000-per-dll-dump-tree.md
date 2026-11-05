---
managed-by: Skill(llm-subtask)
status: active
---

# Per-DLL dump tree: `dlls.list` → `dlls.json/` → `dlls.tsv/`

**Priority:** next up (agreed with the user 2026-11-05; session 2ac92f5f ran out)
**Complexity:** medium-high: a Windows-side ctypes scanner driven from WSL redo, plus two WSL views
**Context:** `docs/dev/convar-dump.kb/` (read all of it; `output-views.md` is the agreed layout)

## Problem Statement

Dump every convar and concommand declaration out of the game DLLs, offline,
deterministically, losslessly (duplicates kept), one independent target per
DLL so `redo -j` parallelises, and commit TSV views for `git diff` across
patches. The per-DLL JSON is meant to grow more sections later (interfaces,
logging channels, schemas).

## Current Situation

Prototyped, not built. Everything lives in `scratchpad/` (Windows Python,
run from WSL; see "Running the probes" below):

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
  defaults equal GameTracking's DumpSource2 dump (`trash/upstream/convars.txt`,
  gitignored; the 11 others are engine2/client-owned names reading zero).

## Proposed Solution

As `docs/dev/convar-dump.kb/output-views.md` lays out: `data/dlls.list`
(gitignored), `data/dlls.json/<dll>.json` (gitignored, one Windows-side scan
per DLL), `data/dlls.tsv/{convars,concommands}.tsv` (committed, one row per
declaration, sorted by name, module, index). Mirror the existing
`data/gamedata.list.do`, `data/gamedata.json/default.json.do`,
`data/gamedata.tsv/default.tsv.do` (guards, `redo-stamp`, case table).

Split the scanner so the parsing is testable under WSL pytest: a tiny
Windows-only memory reader (ctypes `LoadLibraryExW` + `ReadProcessMemory`) and
pure functions that walk queues and decode entries through a `read(addr, n)`
callable, which a test can back with a fake memory dict. The scanner runs
under Windows Python by path, stdlib only (no venv there), and writes one JSON
document to stdout.

## Implementation Steps

- [ ] Decode the queue's value fields, against the engine, before building anything
  - [ ] Find `ConVarValueInfo_t`'s offsets inside the 160-byte entry (s2sdk
        `convar.h:630-730`: version, has-default/min/max, three `CVValue_t`,
        callbacks, `m_eVarType`; s2sdk's copy is stale on the type enum, so
        expect drift). Fit them with `hook_probe3.py`'s readback: for names
        declared once, the entry must contain the registry's type code and
        default bytes.
  - [ ] Use the binary's `EConVarType`: `bool int8 uint8 int16 uint16 int32
        uint32 int64 uint64 float32 float64 string color vector2 vector3
        vector4 qangle vectorws` (`registration-flow.md`)
  - [ ] Decode the 64-byte command entry beyond name/help/flags only if it
        holds something worth dumping (callback is a pointer: drop it)
  - [ ] Pass: every once-declared `server` and `client` convar's type, default,
        min, max equal the registry's; record the layout in
        `registration-flow.md` with the build
- [ ] Settle the `rendersystemdx11` owner-check exception (6 of 7 entries pass,
      6851; `queue-shape-scan.md` `[!QUESTION]`): read the odd entry, decide
      whether a null or out-of-image ref is legal, then make the check strict
- [ ] `data/dlls.list.do`: every DLL under `game/bin/win64` and
      `game/citadel/bin/win64` whose PE imports name `tier0.dll`, plus tier0
      (`dll-coverage.md`; 46 on 6851). Import tables via `pefile` (`uv add`,
      reuse before inventing). Minus an exclusion list with a reason each:
      `helpsystem`, `assetpreview`, `propertyeditor`, `toolframework2` hang in
      `LoadLibrary` (unkillable process), `vfx_dx11` fails to load. Never let a
      target load an excluded DLL.
- [ ] Scanner module (Windows side), ≤300 lines, stdlib only, with WSL-side tests
      of its pure part
  - [ ] Pin strides 160 (convars) / 64 (commands); JSON: `{module, build,
        convars: [...], concommands: [...]}`, entries in queue order with
        their index; no addresses; flags as names (`FCVAR_*` from s2sdk
        `convar.h`, lowercased without prefix, matching DumpSource2's
        spelling), unknown bits `flag_<n>`; undecodable values as hex
  - [ ] All `validation.md` shape checks fail the scan (non-zero exit)
  - [ ] Process hygiene: `os.add_dll_directory` both bin dirs; cwd a scratch
        dir (Windows Python writes `*.mdmp` into cwd on an access violation);
        exit via `TerminateProcess` so DLL detach doesn't run static
        destructors
- [ ] `data/dlls.json/default.json.do`: guard on `dlls.list`; run
      `python.exe "$(wslpath -w scanner)" "$(wslpath -w dll)"` with a timeout;
      depend on the scanner source, `data/deadlock-version.json`, the DLL file
- [ ] `data/dlls.tsv/default.tsv.do` + `src/deadlock/convars.py`,
      `src/deadlock/concommands.py` (tests beside): one `redo-ifchange` over
      every `dlls.json/<dll>.json` from `dlls.list`, then format
- [ ] Wire up: `.gitignore` exceptions for `data/dlls.tsv/*.tsv` and the
      `*.do` files (pattern as `gamedata.tsv`); add both views to `all.do`'s
      `committed` list (`redo-adopt`); README views table
- [ ] Check target: re-learn the strides from `server.dll` (pass 1 of
      `queue-shape-scan.md`), fail if they differ from the pinned ones
- [ ] On-demand checks: registry readback for `server`/`client` (port
      `hook_probe3.py`'s compare to the JSON), and the `cvarlist` oracle
      (`capture-approach.kb/runtime-cvarlist.md`)
- [ ] Docs: drop each `[!TODO]` callout as it lands; record the tool choice in
      `docs/dev/decisions.kb/` (it departs from `reuse-existing-parsers.md`,
      `convar-dump.kb/CLAUDE.md` says why that matters); rewrite
      `capture-approach.md` as the answer once its `[!QUESTION]` closes
- [ ] Commit (`Command(commit)`)

## Open Questions

- `all.do` on a host without Windows Python: skip the dll views, or fail?
  Only this WSL box exists today; ask the user before deciding.
- The engine's merged view (later, separate): the merge rule, the 5
  unexplained flag changes, the 11 zero defaults, whether tier0's own queue
  (`find`, `cvarlist`) registers only in tier0's `Init`, its scope (all DLLs
  is the default). All in `output-views.md` / `icvar-hook.md` `[!QUESTION]`s.

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
trash/hook && python.exe "$(wslpath -w ../../scratchpad/hook_probe3.py)"
server.dll Source2ServerConfig001`. The probes hardcode the stock
`C:\Program Files (x86)\Steam` install; the real scanner takes the DLL path
as an argument, which the `.do` derives from `DEADLOCK_HOME` (`python -m
deadlock.paths`, `wslpath -w`). `python.exe` (Windows 3.14) is on the WSL `PATH` and
accepts a `\\wsl.localhost\…` script path; run from a scratch dir.
Disassembly and PE parsing in WSL without touching the project deps:
`uv run -q --no-project --with capstone --with pefile python …`; helpers in
`trash/hook/` (`disas.py`, `xref_global.py`, `mdmp_exc.py`, gitignored).

Steam patched 6851 → 6854 mid-session (2026-11-05 20:29); the game install
is unusable while Steam updates (`citadel/bin/win64/` empties). Numbers in the
KB are labelled by build.
