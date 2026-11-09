---
managed-by: Skill(llm-subtask)
status: done
---

# dllscan skeleton and memory

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Wave 1: package skeleton + `dllscan.memory`)
**Context:** `docs/dev/cvar-dump.kb/` (`queue-shape-scan.md`, `validation.md`,
`windows-python-host.md`); prototype `docs/dev/probes/convar_scan.py`

## Problem Statement

Create the `src/dllscan/` package skeleton and its `memory` module, the base
the `image` and `reglist` waves build on. Scope, only: `pyproject.toml` (hatch
packages), `__init__.py` (docstring), `stdlib_only_test.py` (`ast` check: no
import outside `sys.stdlib_module_names` and `dllscan`), `memory.py` +
`memory_test.py`: `Read = Callable[[int, int], bytes | None]` (None if
unreadable, never raises); `Memory` with `u32`, `u64`, `cstr_in(addr, lo, hi)`;
`Segments`, a `{base: bytes}` fake callable as a `Read`. Stdlib only,
3.12-compatible, ≤300 lines/module, TDD (observe each assertion fail). Siblings
own `flags`, `document`. No git staging/commits; don't edit the parent plan.

## Implementation Steps

- [x] `pyproject.toml`: `src/dllscan` in hatch packages; `uv sync`
- [x] `__init__.py` docstring
- [x] `stdlib_only_test.py`; each assertion observed failing under mutation
- [x] `memory_test.py` (red), then `memory.py` (green); refusal tests driven red by 10 mutants, all killed
- [x] `pytest src/dllscan`, `pyright src/dllscan` clean
- [x] Final report here; `status: done`

## Decisions

- `stdlib_only_test` skips `*_test.py`: tests run WSL-side under pytest and
  never ship to `python.exe`. Relative imports are `dllscan` by definition.
- `u16` added beside `u32`/`u64`: `image` needs it for the PE header
  (`NumberOfSections`, `SizeOfOptionalHeader`).
- Integer reads return `int | None`; None is the caller's misfit signal, as
  in the prototype's `qword`. No exceptions for bad addresses.
- `cstr_in` "printable" = strict UTF-8 whose every char `isprintable()` or is
  `\t\r\n`; empty allowed. Help text needs spaces/newlines; the name-only
  rule (prototype `[\x21-\x7e]{1,127}`) is `reglist`/`entries`' to apply.
- `MAX_CSTR = 4096` bytes before the NUL (hook_probe3's cap); longer → None.
- `cstr_in` reads in chunks up to the next 4 KiB page boundary (real
  readability is page-granular), falling back to single bytes when a chunk
  fails, so a fake whose segment ends off the page grid still works.

## Open Questions

- [ ] The printable rule is unchecked against real help text; if a real help
      string holds a char it rejects, its entry misfits. The first real scan
      (Wave 4) settles it.

## Final report

Files: `pyproject.toml` (hatch `packages` += `src/dllscan`; `uv.lock`
unchanged), `src/dllscan/{__init__,memory,memory_test,stdlib_only_test}.py`.

`dllscan.memory` API (all reads never raise for a bad address):

- `type Read = Callable[[int, int], bytes | None]`: `read(addr, n)` → the `n` bytes, or None if any is unreadable
- `MAX_CSTR = 4096`, `PAGE = 4096`
- `class Segments(dict[int, bytes])`: `Segments({base: data})(addr, n)` → bytes if `[addr, addr+n)` lies inside one segment, else None
- `class Memory(read: Read)`: `.read` is the callable, public (for bulk section reads)
  - `u16/u32/u64(addr) -> int | None`: little-endian; None if unreadable
  - `cstr_in(addr, lo, hi) -> str | None`: the string if `lo <= addr < hi`, string+NUL inside `[lo, hi)`, readable, ≤ `MAX_CSTR` bytes, printable (above); else None

Checks: `pytest src/dllscan` 26 passed (19 memory, 6 stdlib-only, 1 doctest);
`pyright src/dllscan` 0 errors. Under this harness `bin/shell` needs
`env -u DIRENV_DIR -u DIRENV_DIFF -u DIRENV_WATCHES -u DIRENV_FILE` first.
