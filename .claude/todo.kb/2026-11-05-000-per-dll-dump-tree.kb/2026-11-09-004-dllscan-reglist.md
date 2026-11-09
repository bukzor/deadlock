---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-09-003-dllscan-image-layout.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-001-dllscan-skeleton-and-memory.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-003-dllscan-image-layout.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/cvar-dump.kb/capture-approach.kb/queue-shape-scan.md
  - docs/dev/cvar-dump.kb/validation.md
  - docs/dev/cvar-dump.kb/registration-flow.md
  - docs/dev/probes/convar_scan.py
  - docs/dev/probes/fixed_stride_scan.py
---

# `dllscan.reglist`: find and walk the reg-list queues

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Wave 3; module
table under "`src/dllscan/`", row `reglist`)

## Problem Statement

Port the queue shape scan from the probes into `dllscan.reglist`, over
`memory.Memory` and `image.Image` (APIs: the Final reports of 001 and 003).
The plan's row fixes the surface; refine signatures as needed and report
them exactly:

- `walk(mem, head, stride, image)`: entry addresses in replay order, or
  `None` on misfit (a broken link or an entry that fails the shape test).
- `find_heads(mem, image, stride)`: candidate heads over the image's
  writable sections, with the owner check. Its callers want "at most one head
  per kind"; return what was found and let the caller decide (and say how a
  second head shows up).
- `learn_strides(...)`: pass 1 from the probes, which re-derives the
  strides from a DLL instead of trusting the pin.
- `STRIDES = {"convars": 160, "concommands": 64}`, pinned.

**Decided for you:**
- Misfits raise `shape.ShapeError` where the plan or `validation.md` calls it
  a shape violation. `None` is only for "this candidate is not a queue"
  during the search. Keep the two apart and document which is which.
- The name rule `memory.cstr_in` deliberately left out belongs here (or in a
  helper `entries` will reuse): the probe's `[\x21-\x7e]{1,127}`, non-empty
  with no spaces. Help text is not checked here.
- No queue index is stored anywhere. Order is position (`6c0550f`).
- Out of scope, do not settle: the `rendersystemdx11` owner-check exception
  (`queue-shape-scan.md` `[!QUESTION]`). Implement the check strictly, as the
  probe does, and record in Open Questions how a lenient variant would plug
  in. Also out: value-field decoding and `entries`.

**Tests:** synthetic queues built with `image_fake` (extend that module only
if `reglist` needs a fixture it lacks, and report it), covering: a two-queue
image, a broken link, a non-owner pointer, a name that fails the rule, a
second head of the same kind, and a stride mismatch for `learn_strides`.
There is no real-memory check this wave: that needs `win32` (wave 4).

**Scope:** `src/dllscan/reglist.py`, `src/dllscan/reglist_test.py`, and
`src/dllscan/image_fake.py` for additive changes only.

## Steps

- [x] TDD (35 tests red on a stub; 42 mutants, `trash/reglist-mutants/run.py`, 3 survive, all equivalent: the `m_nSize <= 100` bound, since entry 100 would sit on `m_pPrev`, never a name, and two perf prefilters); `pytest src/dllscan` 96 passed; `pyright src/dllscan` 0 errors

## Decisions

- One entry test, inside `walk`: name per `NAME`, help null or in the image, trailing ref in a writable section (so `learn_strides` owner-checks too, unlike the probe). Heads must point outside the image (static name-led tables exist); an `m_pPrev` cycle is `None`.
- `ShapeError` only where the result would be wrong rather than empty: a writable section unreadable, or a head that more than one stride fits over >1 block. Every other misfit in the search is `None`.

## Open Questions

- [ ] Lenient owner check (`rendersystemdx11`): lift the ref test out of `_fits` into `find_queues` as a per-queue tolerance (null refs, or k misses), leaving `walk` and `learn_strides` strict.

## Final report

- Files (new): `src/dllscan/reglist{,_test}.py`; `image_fake` unchanged (the queue builder, `Fake`, lives in the test). Deviation: `find_heads` is `find_queues`, returning the walked entries (every caller wants them; a re-walk reads twice).
- API: `BLOCK = 100`; `STRIDES = {"convars": 160, "concommands": 64}`; `CANDIDATE_STRIDES = range(16, 1024, 8)`; `NAME = re.compile(r"[\x21-\x7e]{1,127}")` (fullmatch); frozen `Queue(head: int, stride: int, entries: tuple[int, ...])`: `head` is the `s_pRoot` slot's address, `entries` the entry addresses in replay order.
- `name_at(mem, addr, image) -> str | None` (for `entries`); `walk(mem, root, stride, image) -> tuple[int, ...] | None` (`root` = the slot's value, the newest block); `find_queues(mem, image, stride) -> list[Queue]`, address order: a second head of one kind is a second element, the caller raises; `learn_strides(mem, image, strides=CANDIDATE_STRIDES) -> list[Queue]`: heads one stride fits over >1 block; the caller compares their strides to `STRIDES` and labels them by anchors.
- For the coordinator: in-place mutant runs can import stale `__pycache__` (a same-size mutant written within the same second reuses the pyc); this run deletes reglist's pyc and runs `-B`. Earlier waves' mutant tallies may be affected.
