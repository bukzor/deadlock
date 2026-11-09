---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-09-020-convars-atom-aggregate-check.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-006-dllscan-entries-names-help-flags.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-018-convar-value-layout-fit.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-019-dllscan-convar-decode.md
  - docs/dev/convar-dump.kb/CLAUDE.md
  - docs/dev/convar-dump.kb/registration-flow.md
---

# The queue entries' layout as `ctypes` structs: one source for the offsets

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (scanner upkeep)

## Problem Statement

The entry layout is written down twice: as offset constants in
`dllscan.entries` and `dllscan.values`, and as a table in
`registration-flow.md`. Make the code the one source, as packed
`ctypes.LittleEndianStructure`s (`_pack_ = 1`; stdlib, so the stdlib-only
rule holds). They read line for line like the C header, so they still diff
against s2sdk's `convar.h`.

- **One struct per C struct.** `CVarCreationBase_t` is the prefix both entry
  kinds share; `CVValue_t` is 16 bytes. Then the 160-byte convar entry and
  the 64-byte command entry, with the pads and pointers spelled out as
  fields, named as s2sdk names them where it does. The unaligned value
  fields at +31/+47/+63 are the reason for `_pack_ = 1`.
- **Decode through the structs** (`from_buffer_copy` on the entry's bytes)
  and delete the offset constants they replace.
- **Tie sizes to existing knowledge instead of restating it:** a test asserts
  `ctypes.sizeof` of each entry struct equals `reglist.STRIDES[kind]`, and
  each field's `.offset` matches what 018 fitted.
- **DRY a bit beyond that:** where else is one layout fact written down
  twice, in code or between code and docs (e.g. `image`'s PE header offsets,
  `reglist`'s block layout)? Single-source the cheap ones and list the rest
  in Open Questions. Don't build a framework.
- **Docs:** `registration-flow.md`'s offset table shrinks to what the code
  can't say: the evidence (the registry fit, build 6860, the type-table
  RVA) and a pointer to the module.

**Acceptance (6860):**
- `pytest src` passes, and `pyright` is clean on the touched files.
- `redo data/dlls/convars.tsv data/dlls/concommands.tsv data/dlls.check/strides`
  rebuilds every atom, and `git diff data/dlls/` is empty. All 182 atom
  documents are byte-identical to a snapshot taken before the change: this
  is a refactor.

**Scope:** `src/dllscan/` (a new layout module, `entries`, `values`, and their
tests; others only for the DRY items you take), and `registration-flow.md`.
**Start editing `src/dllscan/` only once 020's file says `status: done`:** its
real build runs the scanner from those files.

## Steps

## Decisions

## Open Questions

## Final report
