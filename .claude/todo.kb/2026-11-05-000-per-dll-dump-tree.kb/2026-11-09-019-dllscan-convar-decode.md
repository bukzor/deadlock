---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-09-018-convar-value-layout-fit.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-018-convar-value-layout-fit.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-006-dllscan-entries-names-help-flags.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-008-dllscan-main-load-concommands-strides.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-017-find-queues-by-kind-and-reglist-fake.md
  - docs/dev/convar-dump.kb/registration-flow.md
  - docs/dev/convar-dump.kb/output-views.md
  - docs/dev/convar-dump.kb/validation.md
---

# `dllscan`: decode convars, and the `convars` subcommand

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (step "Decode the
value fields against the engine")

## Problem Statement

Build the decoder from 018's report and the layout in `registration-flow.md`.
The decoding rules, shape checks and pass check are already settled there,
so implement them as stated.

- **`dllscan.values`:** the binary's `EConVarType` table (codes 0–17), and
  `CVValue_t` bytes → a JSON value per type. Each shape check 018 lists
  raises `ShapeError`, including its two suggested invariants: an absent
  value is all zero, and a present value's bytes past its size are zero.
- **`entries.decode_convar(mem, addr, image) -> document.ConVar`:** built on
  `decode_creation_base`, as 006's report says it extends.
- **`document.ConVar`** gains `version: int`. A sibling (020) builds against
  exactly that shape, so add no other field.
- **`facets.convars` + `__main__ convars DLL`**, following the `concommands`
  pattern (008, 017).
- **Docs:**
  - `icvar-hook.md`'s `[!QUESTION]` on the 11 zero defaults is answered by
    018: they are `server`'s `reference` declarations, with has-default 0.
    State it as fact.
  - Drop the `output-views.md` and `registration-flow.md` `[!TODO]`
    callouts this lands.

**Tests:** synthetic entries for every type, including the six unused on
6860 (int8, int16, int64, float64, qangle, vectorws). Also every shape
error, and an absent value.

**Real run (6860):**
- `bin/winpy dllscan convars` over every DLL whose `load` document says `ok`:
  6223 convars, 30 DLLs with a queue (`server` 2008, `client` 2289).
- A second run is byte-identical.
- Re-run 018's pass check (`trash/valuefit/check.py`) against these
  documents and reproduce its numbers.
- Show a few decoded entries: a float, a color, a string, a `reference`
  entry.

**Scope:** `src/dllscan/{values,values_test,entries,entries_test,document,facets,facets_test,__main__}.py`,
`docs/dev/convar-dump.kb/{capture-approach.kb/icvar-hook.md,output-views.md,registration-flow.md}`,
and `trash/`.

## Steps

- [x] `values`: 61 red against a stub (NotImplementedError), then green
- [x] `entries.decode_convar`, `document.ConVar.version`: 29 red, green
- [x] `facets.convars`, `__main__ convars`: 3 red, green
- [x] 39 mutants (`trash/convars019/mutants.py`, `-B`, pyc deleted): 38 killed; every new test red under one
- [x] Docs: `icvar-hook.md`, `output-views.md`
- [x] Real run (6860), twice; 018's pass check over the documents (`trash/convars019/`)
- [x] `pytest src` 698 passed; `pyright` on the 8 files 0 errors

## Decisions

- **Layout in `entries`, types in `values`:** `values` is pure over the 16 bytes (+ `Memory` for a
  string) and raises `ShapeError(what, *detail)`; `decode_convar` reads the 160 bytes once and
  re-raises as `ShapeError(what, hex(entry), *detail)`, 006's shape.
- **NaN/±inf → `ShapeError("convar float", …)`:** JSON can't hold them, and none occurs on 6860.
- **float32 shortest round-trip:** `%.{1..9}g`, first that packs back to the same bits; a
  candidate that overflows float32 (`FLT_MAX`) is skipped. Surviving mutant `range(2, 10)` is
  equivalent: a 1-digit value prints the same at 2 digits.
- **`version` after `type`** in `ConVar`. `ConVarValue`'s docstring drops the hex/`type_<n>`
  fallback: every type decodes. `facets._queue(…, kind)` now serves both facets.

## Open Questions

- [ ] Out of scope, now stale: the parent plan's `values` row ("undecodable to hex").

## Final report

Files: `src/dllscan/` new `values{,_test}.py`; edited `{entries,facets}{,_test}.py`, `document.py`,
`__main__.py`. Docs: `icvar-hook.md` (the 11, as fact; its other two questions stay), `output-views.md` (JSON rules as built).

API:
- `values.SIZE = 16`; `values.TYPES: Mapping[str, int]` (name → size, code order 0-17);
  `values.type_name(code: int) -> str`; `values.decode(mem, type: str, has: int, raw: bytes) -> ConVarValue | None`.
- `entries.decode_convar(mem: Memory, addr: int, image: Image) -> document.ConVar`.
- `document.ConVar`: `name, help, flags, type, version: int, default, min, max`.
- `facets.convars(mem, image, dll: str) -> ConVarsDocument`; CLI `bin/winpy dllscan convars
  DLL [DIR ...]`, invoked exactly as `concommands`.

Real run, 6860, all 91 `ok` DLLs: 6223 convars, 30 with a queue (server 2008, client 2289,
engine2 423); empty stderr; run 2 byte-identical. Absent default/min/max 181/6017/6043;
has-default 0 on exactly the 181 `reference` entries; version nonzero on 10.

Pass check (once-declared, vs 018's registry readback, both sides decoded by `values`):

| dll | once | type | min | max | default | version |
|---|---|---|---|---|---|---|
| server | 1999 | 1999 | 1999 | 1999 | 1980 | 1980 |
| client | 2226 | 2226 | 2226 | 2226 | 2157 | 2157 |

Every mismatch is a `reference` declaration (document `null`/0, registry zero value/-1).
Client default is 2157, not 018's 2158: `snd_soundmixer` (reference, string) decodes to `null`
here and the registry's null `CUtlString` to `""`; 018's check read a null string as `None`.

Samples: `sv_client_min_interp_ratio` float 0.0/0.0/19.0; `citadel_sat_volume_sat_color`
`[255, 255, 255, 255]`; `citadel_steamlearn_new_player_thresholds` `"0=50, 10=60, 20=80, 30=100"`;
`engine_frametime_warnings_enable` (reference) bool, all `null`; `sv_specspeed` version 2.

Deviations: none in API; `registration-flow.md` had no `[!TODO]` left to drop (018 wrote it as fact).
