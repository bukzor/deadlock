---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-013-reglist-per-kind-ref-check.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-008-dllscan-main-load-concommands-strides.md
---

# `find_queues` by kind; `reglist`'s test fake in its own module

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (013's two follow-ups)

## Problem Statement

Two refactors, with no change in behavior:

- **`reglist.find_queues(mem, image, kind)`**: the kind is a `STRIDES` key, and
  it picks both the stride and the ref test. Today the function takes a
  stride and maps it back to a kind. Update `dllscan.facets` and every other
  caller.
- **`reglist_test.py` is 333 lines, over the 300 limit.** Move its `Fake`
  queue builder into a non-test module, `dllscan/reglist_fake.py`, beside
  `image_fake.py`, and import it from both `reglist_test.py` and
  `facets_test.py`.

**Acceptance:**
- `pytest src` passes, and `pyright` is clean on the touched files.
- On the real install (6860), `redo data/dlls/concommands.tsv data/dlls.check/strides`
  rebuilds the atoms, and `git diff data/dlls/` is empty: every output is
  unchanged.

**Scope:** `src/dllscan/{reglist,reglist_test,reglist_fake,facets,facets_test}.py`
and any other caller of `find_queues`. A sibling (018) works only in `trash/`
and `docs/`.

## Steps

- [x] Tests call `find_queues(mem, image, kind)`: 7 red (`ValueError` in the stride→kind unpack)
- [x] `find_queues` by kind; `facets.py` and the `trash/` drivers that call it; 5 mutants (`trash/fq017/mutants.py`, `-B`, pyc deleted), all killed
- [x] `Fake` to `reglist_fake.py`, with a doctest (seen red); both tests import it
- [x] `pytest src`, `pyright`; real install (6860): `redo`, outputs unchanged

## Decisions

- `kind: str`, not a `Literal`: `STRIDES`/`REF_TESTS` are `str`-keyed, and an unknown kind is a `KeyError` at the lookup. A `Literal` would be a type change across `facets`/`ANCHORS` for no runtime gain.
- `reglist_fake.py` takes `Fake` with the constants and `Entry` it needs (`BASE`, `RDATA`, `DATA`, `SECTION_SIZE`, `HEAP`); `addresses` and `CONVAR`/`COMMAND` stay in `reglist_test.py` (test-side expectations, not the fake). Module docstring + doctest as in `image_fake.py`.
- `trash/` drivers counted as callers: `help-census/convars_driver.py`, `winpy/{main008_queues,rdx_time,rdx_scan}.py` now pass the kind. `trash/probe/flagcheck.py` calls the old `convar_scan` probe, not `dllscan`: untouched.

## Open Questions

## Final report

Files: `src/dllscan/reglist.py` (159 lines), `reglist_test.py` (333 → 261), `reglist_fake.py` (new, 90), `facets.py` (one line), `facets_test.py` (import); `trash/` drivers above. No git index.

API (`dllscan.reglist`): `find_queues(mem: Memory, image: Image, kind: str) -> list[Queue]`; `kind` is a `STRIDES` key and selects `STRIDES[kind]` and `REF_TESTS[kind]`. Everything else unchanged.

API (`dllscan.reglist_fake`): `BASE, RDATA, DATA, SECTION_SIZE, HEAP: int`; `type Entry = tuple[int, int, int]`; `class Fake` with `string(text) -> int`, `qword(value=0) -> int`, `entry(name=b"sv_x", help=None, ref=None) -> Entry`, `heap_ref(value=UNREGISTERED) -> int`, `queue(stride, entries) -> tuple[int, list[int]]`, `poke(addr, fmt, value)`, `load() -> tuple[Memory, Image]` (unchanged from `reglist_test.Fake`).

Checks: `pytest src` 505 passed; `pyright` on the five files 0 errors.

Real install, build 6860: `redo -j8 data/dlls/concommands.tsv data/dlls.check/strides` rebuilt all 91 atoms and the strides check (exit 0). `git diff data/dlls/ data/dlls.check/` empty; the 91 gitignored atom JSONs and the strides output are byte-identical to a pre-run snapshot (`trash/fq017/before/`). `concommands.tsv`: 1418 rows.

Deviations: none.
