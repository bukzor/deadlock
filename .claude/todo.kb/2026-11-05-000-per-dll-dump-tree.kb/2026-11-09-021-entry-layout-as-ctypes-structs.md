---
managed-by: Skill(llm-subtask)
status: done
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

- [x] Snapshot: 182 atoms + 3 check outputs, `trash/021/before.sha256`
- [x] `convar_h`: 30 sizes/offsets tests red against a stub, then green
- [x] `entries`, `values` decode through the structs; offset constants gone
- [x] DRY sweep (`reglist`); `registration-flow.md` layout section shrinks
- [x] `pytest src`, `pyright`; `redo` rebuild, atoms byte-identical
- [x] Mutants (`trash/021/mutants.py`, `-B`, pyc deleted): 30 of 30 killed

## Decisions

- **Module `convar_h`:** it transcribes one header, so the name says where to diff
  it. Class names are s2sdk's; `ConVarRegList::Entry_t` → `ConVarRegList_Entry_t`.
- **Natural alignment, no `_pack_`, no pad fields** (deviates from the brief): the
  header declares the values `uint8[16]` ("to prevent align issues"), alignment 1,
  so the compiler's own padding puts them at 31/47/63 and the pointers at 80; ctypes
  pads alike, and the field list is the header's, line for line.
- **Derived structs list `*CVarCreationBase_t._fields_` first**, not subclass: same
  layout, and every struct can be `@final`, which basedpyright needs to accept an
  unannotated `_fields_`. Fields code reads are annotated with a placeholder (`= 0`)
  that ctypes replaces (probed on 3.12 and 3.14).
- **`CVValue_t` is `uint8[16]`, not a union:** its members would restate
  `values.TYPES`; a test ties `sizeof` to `max(TYPES.values())`.
- **`decode_convar` reads the entry once:** identical output; a partly readable
  entry with a bad name now reports "entry unreadable" before "entry name".
- **Test fakes keep their hand-packed layouts** (`entries_test.info`, `reglist_fake`,
  `image_fake`): the independent second statement the code is checked against.

## Open Questions

- [ ] `image`'s PE headers as ctypes structs would replace its inline offsets (0x3C,
      +4, +6, +0x14, +56) but change its per-field "X unreadable" errors. Not cheap.
- [ ] `deadlock.dlls_convars.TYPES` restates `values.TYPES`' names in code order
      (`src/deadlock`, out of scope).
- [ ] `reglist`'s block (`u32 m_nSize; Entry_t[100]; prev`) stays constants
      (`BLOCK`, `_ENTRIES`): a struct per stride is the framework the brief rules out.

## Final report

Files: new `src/dllscan/convar_h{,_test}.py`; edited `entries{,_test}.py`, `values.py`,
`reglist.py`, `registration-flow.md` (tables gone; evidence kept, points to `convar_h.py`, `values.py`).

API (`dllscan.convar_h`): `CVValue_t = c_uint8 * 16`; `@final` `LittleEndianStructure`s
`CVarCreationBase_t`, `CompletionCallbackInfo_t`, `ConVarValueInfo_t`, `ConVarCreation_t`,
`ConVarRegList_Entry_t` (160), `ConCommandCallbackInfo_t`, `ConCommandCreation_t`,
`ConCommandRegList_Entry_t` (64), s2sdk's field names; `offset_of(struct: type[ctypes.Structure],
path: str) -> int` (dotted path). `values.SIZE = ctypes.sizeof(CVValue_t)`; `entries`' API unchanged.

Checks (6860): `pytest src` 730 passed; `pyright` (repo) 0 errors. `redo` of the three targets,
forced by touching a scanner module, rebuilt all 182 atoms and `strides`: all 185 files of
`trash/021/before.sha256` identical, `git diff data/` empty. Mutants: 30 of 30 killed, and each of
the 30 new test ids observed red (`trash/021/{mutants.log,red-ids.txt}`).

Deviations: no `_pack_` or pad fields (Decisions).
