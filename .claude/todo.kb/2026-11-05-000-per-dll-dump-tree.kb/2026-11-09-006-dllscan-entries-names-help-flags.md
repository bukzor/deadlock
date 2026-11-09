---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-09-004-dllscan-reglist.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-000-dllscan-document-types.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-002-dllscan-flags-table.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-003-dllscan-image-layout.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-004-dllscan-reglist.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/convar-dump.kb/registration-flow.md
  - docs/dev/convar-dump.kb/validation.md
  - docs/dev/probes/convar_scan.py
---

# `dllscan.entries`: decode name, help, flags from queue entries

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Wave 4; the
`entries` row under "`src/dllscan/`")

## Problem Statement

Decode one queue entry, given its address from `reglist.Queue.entries`, into
the parts we already know how to read: **name, help, flags**. Both kinds are
covered: the 64-byte concommand entry and the 160-byte convar entry. The
offsets come from `docs/dev/probes/convar_scan.py` and `registration-flow.md`.
Cite each offset's source in the code.

- `decode_concommand(mem, addr, image) -> document.ConCommand`, complete.
- The convar entry's value fields (type, default, min, max) are **not** in
  this unit. A later unit fits their offsets against the engine's registry. So
  don't return a `document.ConVar` with invented values. Expose what is
  decodable now, under a name that leaves room for the later full
  `decode_convar`, and say exactly how the later unit extends it. Changing
  `document` is out of scope; if the document types get in the way, raise it
  in Open Questions.
- Name via `reglist.name_at`, which applies `reglist.NAME`. Help via
  `Memory.cstr_in` within the image range; a null help pointer is legal.
  `flags.names` gives the flag names.
- Every shape check `validation.md` assigns to entry decoding raises
  `shape.ShapeError`, with the entry address in the message. A misfit here is
  a bug or a layout change, never "not a queue".
- No addresses or queue index go into the output (order is position).
- Docstrings say what the names and types don't; a type like `str | None`
  needs no sentence restating it (here and in the `document.py` lines you
  touched).

**Tests:** synthetic entries built with `image_fake`, or the queue builder in
`reglist_test.py`; if you need it in a second test file, move it into a
non-test module and report the move. Cover: a full concommand, a null help,
an unknown flag bit, a bad name, help outside the image, and an unreadable
entry. There is no real-memory check in this unit: wave 5's `__main__` run
does that.

**Scope:** `src/dllscan/entries.py`, `src/dllscan/entries_test.py`, plus the
fixture move if you make one.

## Steps

- [x] Tests against a stub: all 21 red
- [x] Implement; green. 18 mutants (`trash/entries-mutants/run.py`, `-B`, pyc
      deleted): all killed, and every test id is red under at least one
- [x] Help census on the real install (6860)
- [x] `pytest src/dllscan` 131 passed; `pyright src/dllscan` 0 errors

## Decisions

- **Offsets:** `CVarCreationBase_t` (s2sdk 18139bd `convar.h:157-167`), the
  prefix of both creation structs, which lead `Entry_t`: name +0, help +8,
  flags +16 (u64). Read as one 24-byte read, so a partly readable entry is
  "unreadable" too.
- **Convar partial:** `decode_creation_base` → `CreationBase` (name, help,
  flags), not a `ConVar`. "base" follows s2sdk's name for the struct.
  `decode_concommand` returns it unchanged (the rest of the 64 bytes is a
  callback pointer).
- **Shape checks here:** the entry is readable; the name passes `name_at` (in
  the image and matching `NAME`); the help is null, or `cstr_in` inside the
  image. The trailing-ref check needs the stride, so it stays in `reglist.walk`.
  The type and has-value checks belong to `decode_convar`. Errors are
  `ShapeError(what, hex(entry), …)`, where `what` is `"entry unreadable"`,
  `"entry name"` or `"entry help"`.
- **No fixture move:** a 64-byte entry needs no queue. `entries_test.Fake` is
  local, about 20 lines.

## Final report

- Files: new `src/dllscan/entries.py`, `src/dllscan/entries_test.py`; edited
  `src/dllscan/document.py` (`help: str | None` in `ConCommand`/`ConVar`;
  `LoadOk` docstring: the modules the load added) and
  `src/dllscan/facets_test.py:46,48` (expected `help` for a null pointer).
- API:
  - `class CreationBase(TypedDict): name: str; help: str | None; flags: Sequence[str]`
    (structurally a `document.ConCommand`; `flags` is a `tuple` from `flags.names`).
  - `decode_creation_base(mem: Memory, addr: int, image: Image) -> CreationBase`
  - `decode_concommand(mem: Memory, addr: int, image: Image) -> document.ConCommand`
  - Both raise `shape.ShapeError` as described in Decisions.
- How the later unit extends it: add `decode_convar(mem, addr, image) -> ConVar`
  as `ConVar(**decode_creation_base(mem, addr, image), type=…, default=…,
  min=…, max=…)`, raising `ShapeError` on an unknown `EConVarType` or a
  has-value byte other than 0 or 1.
- Help census, 6860, the 91 DLLs that load (97 minus the four hang-listed;
  `phonon4`, `vfx_dx11` fail `LoadLibraryExW: 126`). Convars via
  `trash/help-census/convars_driver.py`, commands via `bin/winpy dllscan
  concommands`; outputs and `summarize.py` in `trash/help-census/`.

  | kind | null | `""` | text | total | DLLs with a queue |
  |---|---|---|---|---|---|
  | convars | 3248 | 152 | 2823 | 6223 | 30 |
  | concommands | 24 | 53 | 1334 | 1411 | 29 |

  No help is whitespace-only. Every `reference` convar (181 of 181) has a null
  help. One name can be declared both ways: `voice_loopback_no_networking` is
  null in client (`developmentonly reference defensive`) and `""` in engine2
  (`userinfo`); `audio_input_use_sdl_roles` twice in soundsystem, likewise.
