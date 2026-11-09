---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-09-001-dllscan-skeleton-and-memory.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-001-dllscan-skeleton-and-memory.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/probes/convar_scan.py
---

# `dllscan.image`: a loaded PE image's layout

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Wave 2; module
table under "`src/dllscan/`")

## Problem Statement

Write `dllscan.image`: given a `dllscan.memory.Memory` and the base address
`LoadLibraryExW` returned, read the PE headers through memory and return the
image's layout. It is the second layer of the scanner; `reglist` (wave 3)
consumes it for two things, so shape the API for them:

- the **image range** `[base, base + SizeOfImage)`: the owner check ("this
  pointer points into this DLL") and the `lo, hi` bounds for
  `Memory.cstr_in`;
- the **writable sections**, as address ranges, which `find_heads` scans for
  queue heads (bulk reads via `Memory.read`).

Port the header walk from `docs/dev/probes/convar_scan.py`; keep what the
loaded image needs, nothing more (no imports/exports: that is the later `pe`
facet, WSL-side). A loaded section spans `VirtualAddress` for `VirtualSize`
(fall back to `SizeOfRawData` when `VirtualSize` is 0); writable is
`IMAGE_SCN_MEM_WRITE` (0x80000000). Keep section names (`.data`, …) and
characteristics on the record: lossless at no cost, and the owner check may
want `.rdata`.

Headers that don't fit (no `MZ`, no `PE\0\0`, not PE32+/AMD64, a section
outside the image, unreadable) raise; they never return a partial layout. The
plan puts `ShapeError` in `entries`, but `image` needs it first: decide where
the scanner's one exception type lives (e.g. its own small module) and report
it, since `reglist` and `entries` will raise it too.

API shape is yours (a frozen dataclass is the natural fit); report it exactly.

**Test fixture, reusable:** `reglist`'s tests need a synthetic loaded image
too. Write one builder (headers + sections into a `memory.Segments`) that
both test suites can import, and say where it lives. It must not pull pytest
into a non-test module.

**Real-binary check (not a committed test):** feed the on-disk `server.dll`
header bytes (`python -m deadlock.paths game_dir`; the DLL is under
`game/citadel/bin/win64/`) through `Segments({base: header_bytes})` and
compare section names/RVAs/sizes/writability to `pefile`
(`uv run -q --no-project --with pefile python …`). Note the result in your
Final report.

**Scope (only these files):** `src/dllscan/image.py`, `src/dllscan/image_test.py`,
the fixture module if separate, the exception module if separate.

## Steps

- [x] TDD (21 mutants, all killed); real-binary check; `pytest src/dllscan` 60 passed; `pyright` (4 files) 0 errors

## Decisions

- `ShapeError` lives alone in `dllscan.shape`, so `reglist`/`entries` share it without importing each other. Fixture `dllscan.image_fake`: non-test, stdlib only, beside `image` (as `Segments` is in `memory`).
- Names: NULs stripped, must be printable ASCII. Also raise on `SizeOfOptionalHeader` < 112 (fixed PE32+ part); the table is at `opt + SizeOfOptionalHeader`, not a fixed 0xF0. These are the only deviations.

## Final report

- Files (new): `src/dllscan/{shape,image,image_fake,image_test}.py`. `dllscan.shape.ShapeError(Exception)`: args are unformatted values.
- `dllscan.image`: `WRITE = 0x80000000`; frozen dataclasses
  `Section(name: str, span: range, characteristics: int)` (`span` absolute: `VirtualSize`, or `SizeOfRawData` if 0; `.writable -> bool`) and
  `Image(span: range, sections: tuple[Section, ...])` (`span` = `[base, base+SizeOfImage)`, sections in table order; `.writable -> tuple[Section, ...]`);
  `read_image(mem: Memory, base: int) -> Image`, raising `ShapeError` on: no MZ / PE sig, Machine ≠ AMD64, Magic ≠ PE32+, short optional header, any field or the section table unreadable, bad name, section ending past `span.stop`.
  Uses: owner check `p in image.span`; `cstr_in(a, image.span.start, image.span.stop)`; scan `mem.read(s.span.start, len(s.span))` for `s in image.writable`.
- `dllscan.image_fake`: `FakeSection(name, rva, characteristics, data=b"", virtual_size=None, raw_size=None)` (sizes default `len(data)`); `loaded(base, sections, size_of_image=None) -> Segments`: headers at `base`, each section its own segment at `base+rva`, data zero-padded (default size: last end, 0x1000-aligned); add heap segments to the result. `headers(sections, size_of_image) -> bytearray` to corrupt, at offsets `NT`, `OPT`, `TABLE`.
- Real binary (6860 `server.dll`, 0x400 on-disk header bytes; `trash/image-mutants/real_check.py`): span 0x4985000 and all 5 sections (`.text .rdata .data .pdata .reloc`) equal `pefile`'s name/RVA/size/characteristics; only `.data` writable (VirtualSize 0xeffadc, bss included).
