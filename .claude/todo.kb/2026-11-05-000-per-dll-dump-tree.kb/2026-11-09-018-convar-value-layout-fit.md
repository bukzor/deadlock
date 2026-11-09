---
managed-by: Skill(llm-subtask)
status: open
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

## Decisions

## Open Questions

## Final report
