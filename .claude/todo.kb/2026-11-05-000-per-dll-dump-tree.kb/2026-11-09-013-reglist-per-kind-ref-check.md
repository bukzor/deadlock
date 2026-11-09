---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-09-007-rendersystemdx11-owner-check-evidence.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-004-dllscan-reglist.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-007-rendersystemdx11-owner-check-evidence.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-008-dllscan-main-load-concommands-strides.md
  - docs/dev/cvar-dump.kb/CLAUDE.md
  - docs/dev/cvar-dump.kb/capture-approach.kb/queue-shape-scan.md
---

# `reglist`: the ref check, per queue kind

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the step "Settle the
`rendersystemdx11` owner-check exception")

## Problem Statement

The user accepted 007's recommendation. Today `reglist` applies one ref test
to every entry: the trailing ref must point into the DLL's writable sections.
Make it a predicate per queue kind:

- **Commands:** the ref is readable and the u16 at the ref is `0xFFFF` (an
  unregistered `ConCommandRef`, s2sdk `convar.h:536`). Where the ref points
  doesn't matter, so heap-owned commands (`CConCommandMemberAccessor`) pass.
- **Convars:** keep the owner check as it is.

The predicate is pure over `Memory` and chosen by kind (the `STRIDES` keys).
`walk` and `find_queues` apply the kind's predicate. `learn_strides` runs
before any kind is known: pick the rule it uses, justify it, and keep its
6860 results unchanged. Shape the API so another kind, or a revised rule for
one kind, is a predicate change and doesn't touch the walk.

**Acceptance, on the real install (6860)**, reusing 007's drivers in
`trash/rdx/` and `trash/winpy/` where they fit:
- strict scan over all 91 DLLs that load: 6223 convars, **1418** commands,
  with `rendersystemdx11` yielding its 7 commands, and none of the four
  spurious one-entry queues (stride 160 at `inputsystem`,
  `panoramauiclient`, `vphysics2`, `vscript`);
- `bin/winpy dllscan concommands` on `server.dll`, `client.dll` and
  `engine2.dll` is byte-identical to before the change (008's sha256 for
  `server`: `231ba05b…`), and `rendersystemdx11.dll` gives 7 commands;
- `strides` still passes on all three.

**Tests:** a heap-owned command (its ref outside the image, reading `0xFFFF`)
passes; a command whose ref reads anything else fails; a convar whose ref
is outside the writable sections fails.

**Docs (in scope for this unit):** in `queue-shape-scan.md`, replace the
`[!QUESTION]` callout with the fact as built, starting from the sentence
007 proposes. Make pass 2's "last qword … own writable sections" sentence
say convar entries. Follow `cvar-dump.kb/CLAUDE.md`'s tense rules: plain
prose is fact.

**Scope:** `src/dllscan/reglist.py`, `src/dllscan/reglist_test.py`,
`docs/dev/cvar-dump.kb/capture-approach.kb/queue-shape-scan.md`, and
`trash/`. The `concommands` atoms (011) depend on `src/dllscan/`, so after the
change `redo` rebuilds them; run it and report the new total.

## Steps

- [x] Baseline before the change (6860): `concommands`/`strides` on server, client, engine2, rendersystemdx11 (`trash/reglist013/run.sh before`)
- [x] TDD: tests red on stubs; 12 mutants (`trash/reglist013/mutants.py`, `-B`, pyc deleted), all killed, every new test red under one
- [x] Real runs (`run.sh after`; `trash/reglist013/scan_all.sh` = 007's with a 180 s timeout, summarized by `trash/rdx/summarize.py`); docs; `redo -j8 data/dlls/concommands.tsv`

## Decisions

- `RefTest = Callable[[Memory, int, Image], bool]`, `REF_TESTS` keyed by `STRIDES` key. `walk` takes the test as a parameter; `find_queues` keeps its `stride` signature (facets.py is out of scope) and maps a pinned stride to its kind.
- `learn_strides` uses `owned_ref` at every stride: it is the rule that learned 160/64 before (unchanged by construction), and every multi-block queue on 6860 passes it; the one heap-owned ref sits in a 7-entry queue pass 1 skips. A future miss fails `strides` loudly.
- Baseline is a fresh capture, not 008's sha: `server`'s output moved after 008 (`help: ""` → `null` for missing help), so `231ba05b…` is stale; today's is `47931d9b…`.

## Open Questions

- [ ] `find_queues(mem, image, kind)` would say "chosen by kind" directly; it needs a one-line `facets.py` change.
- [ ] `reglist_test.py` is 333 lines (>300). The fix is moving `Fake` to `reglist_fake.py` (beside `image_fake.py`), which edits `facets_test.py`'s import.
- [ ] `queue-shape-scan.md`'s `[!TODO]` (pin the strides, pass 1 a check target) looks half-built: strides are pinned and `dllscan strides` exists; the `data/dlls.check/strides` target does not.

## Final report

Files: `src/dllscan/reglist.py` (159 lines), `reglist_test.py`, `queue-shape-scan.md` (`[!QUESTION]` → fact paragraph after the 6851 pass-2 evidence, starting from 007's sentence; pass 2 says convar entries are owner-checked). No git index.

API (`dllscan.reglist`), additions and changes:
- `UNREGISTERED = 0xFFFF`; `type RefTest = Callable[[Memory, int, Image], bool]` (`test(mem, ref, image)`).
- `owned_ref(mem, ref, image) -> bool`: ref in a writable section. `unregistered_command_ref(mem, ref, image) -> bool`: `mem.u16(ref) == 0xFFFF`, location-free.
- `REF_TESTS: Mapping[str, RefTest] = {"convars": owned_ref, "concommands": unregistered_command_ref}`.
- `walk(mem, root, stride, image, ref_test) -> tuple[int, ...] | None` (new required param).
- `find_queues(mem, image, stride)`: unchanged signature; `stride` must be a `STRIDES` value. `learn_strides`: unchanged signature, owner-checks.

Real install, build 6860:
- Strict scan, 91 DLLs that load (phonon4, vfx_dx11 fail 126): **6223 convars, 1418 commands**, 30 DLLs per kind; `rendersystemdx11` 7 commands; the four one-entry stride-160 queues are absent (each DLL keeps one convar queue).
- `concommands` server/client/engine2 byte-identical to the pre-change capture (493/428/220; server `47931d9b…`); `rendersystemdx11` 0 → 7. `strides` byte-identical and exit 0 on all three.
- `redo -j8 data/dlls/concommands.tsv`: 91 atoms rebuilt; **1418** rows (was 1411), the diff is rdx's 7 rows. 5 atoms' `module` also changed case (Qt5*, SDL3): sibling 014's concurrent `facets.py` edit, not this one.

Checks: `pytest src/dllscan` 145 passed; `pyright` on both files 0 errors. Deviations: `find_queues` keeps `stride` (above); test file over 300 lines.
