---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-006-dllscan-entries-names-help-flags.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-013-reglist-per-kind-ref-check.md
  - docs/dev/convar-dump.kb/CLAUDE.md
  - docs/dev/convar-dump.kb/registration-flow.md
  - docs/dev/convar-dump.kb/capture-approach.kb/icvar-hook.md
  - docs/dev/convar-dump.kb/output-views.md
  - docs/dev/convar-dump.kb/validation.md
  - docs/dev/probes/hook_probe3.py
---

# The convar entry's value fields: fit the layout against the engine

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the step "Decode
the value fields against the engine", its first two sub-steps and its pass
criterion)

## Problem Statement

Research only; the decoder is a later unit built from your report. The
160-byte convar entry begins with `CVarCreationBase_t` (name, help, flags:
006). The rest holds `ConVarValueInfo_t`: version, has-default/min/max, three
`CVValue_t`, callbacks, and `m_eVarType` (s2sdk `convar.h:630-730`; its type
enum is stale, so expect drift). Find where each field sits, and how each
`EConVarType` is laid out in a `CVValue_t`.

**Method:**
1. Read the entries through the scanner (`reglist.find_queues`, the
   `entries` offsets).
2. Read the registry back through `hook_probe3.py`'s `ICvar` hook: the
   engine's own type code and default for each name.
3. For names declared once, the entry must contain the registry's type code
   and default bytes. Fit the offsets from that, using throwaway drivers
   under `trash/` run through `bin/winpy`.

**Report:**
- **The layout:** each field's offset, size and meaning. Use the binary's
  own `EConVarType` table (`registration-flow.md` lists the names; confirm
  the codes).
- **Decoding rules per type:** each `CVValue_t` to a JSON value whose type
  fits the data (`output-views.md`, JSON content rules). Say which types, if
  any, can't be decoded and why.
- **The pass check, measured:** every once-declared `server` and `client`
  convar's type, default, min and max equal the registry's. Give counts,
  and every mismatch with its cause.
- **The bytes behind has-default/min/max = 0:** what they hold, measured
  across every DLL with a convar queue. Do they carry information a
  lossless store must keep?
- **Whether the 64-byte command entry holds anything beyond
  name/help/flags worth dumping.** The callback is a pointer, so drop it.
- **Docs:** record the layout in `registration-flow.md`, with the build, as
  plain fact (`convar-dump.kb/CLAUDE.md` tense rules).

**Scope:** `trash/` and `docs/dev/convar-dump.kb/registration-flow.md` only.
No `src/` edits: a sibling (017) is editing `src/dllscan/` concurrently, so
import it read-only and expect it to change under you; rerun a driver if an
import fails mid-edit. Never load the hang-listed DLLs
(`deadlock.dll_load.EXCLUDED`).

## Steps

- [x] `trash/valuefit/`: `driver.py` (`queue` | `hook`: Init + readback; Init changed 0 entries),
      `fit.py`, `typetable.py`, `check.py`, `census.py` (all 91 loadable DLLs)
- [x] `registration-flow.md`: layout, type table, command entry (6860)

## Decisions

- Absent value → `null`; that is what has-byte 0 means, and its bytes are all zero.
- Null `CUtlString` → `""`: `CUtlString::Get` returns `""` for null, and no
  queue holds a non-null `""` (219 null, 55 text), so nothing is lost.
- float32 → the shortest decimal that round-trips to the same float32 (`0.02`,
  not `0.019999999552965164`).

## Open Questions

- [ ] `version` (int32 at +24) is engine data (registry +42 agrees) and nonzero
      on 10 `archive` convars; a lossless `ConVar` document needs a `version`
      field. `document` is outside this unit.
- [ ] The doc cites the run by build only; the drivers live in `trash/`.
      Archive `driver.py`/`check.py` into `docs/dev/probes/` if a citation is wanted.
- [ ] `icvar-hook.md`'s `[!QUESTION]` on the 11 zero defaults is answered by
      this: they are `server`'s `reference` declarations (has-default 0).

## Final report

Build 6860; layout in `registration-flow.md` ("The convar entry's layout (6860)"): type
int16 +120; has-default/min/max bytes 28/29/30; values 16 bytes each at 31/47/63 (unaligned);
version int32 +24. Type code = row of tier0's traits table (RVA `0x398610`), 0-17 as listed.

**Decoding rules** (`values`): bool → JSON bool (byte must be 0/1); ints → int; floats →
float (float32 shortest round-trip); string → `str` (pointer to heap, null → `""`);
color → `[r,g,b,a]` ints; vector2/3/4, qangle, vectorws → list of float32. Every type is
decodable. Shape errors: type outside 0-17, a has-byte not 0/1, a non-null string pointer
that doesn't read as a cstr. Suggested checks (they hold on every 6860 entry): an absent
value is all zero; a present value's bytes past its size are zero. No NaN/inf in any queue.
Untested against the registry because unused on 6860: int8, int16, int64, float64, qangle,
vectorws.

**Pass check** (once-declared names, all in the registry once):

| dll | queue | once | type | min | max | default | version |
|---|---|---|---|---|---|---|---|
| server | 2008 | 1999 | 1999 | 1999 (24 present) | 1999 (14) | 1980 | 1980 |
| client | 2289 | 2226 | 2226 | 2226 (92) | 2226 (86) | 2158 | 2157 |

Every mismatch (server 19, client 68 default; 19/69 version) is a `reference`
declaration with has-default 0: tier0 fills in the type's zero value (version -1).
The decode's `null` is right; the 69th, `snd_soundmixer`, is a null-`CUtlString` string.

**Has-X = 0:** across 30 queues and 6223 entries: 181 absent defaults, 6017 mins and
6043 maxes, all 16 zero bytes. They carry no information. has-default is 0 on exactly
the 181 `reference` entries.

**Command entry:** past the base, only pointers, their kind bytes (partly stale) and the
ref: nothing to dump. Likewise the convar's pointers and pads (79, 122-127, 137-143).

Files: `registration-flow.md` (new section, replaces the `EConVarType` paragraph),
`trash/valuefit/`. No `src/`, no index. Deviation: doc cites no script (Open Questions).
