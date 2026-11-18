---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - ./CLAUDE.md   # the protocol only; you change no code
  - ../../../CLAUDE.md   # the repo's standards
  - ../../../apps/vis/
  - ../../../docs/dev/decisions.kb/vis-app.md
---

# Tech advisor: how maintainable is `apps/vis`?

**Parent:** <https:../2026-11-18-000-vis-app.md> (wrap-up)

## Problem Statement

The user asked for a second opinion, as impartial as possible, from a "tech
advisor" on the maintainability of `apps/vis`: its source, tests, tooling and
docs. It was built today, by several agents, in about two hours.

Form your own view from the code. Judge what a developer who is new to the
repo would face when they come to change it in six months, for example to add a
second view or a new kind of damage source, or to follow a game patch. Weigh
it against common practice for a project of this size, not against perfection.

**Deliverable**, in this file's Final report:

- an overall rating out of 10, with the reasoning for it;
- strengths and risks, each pointing at files, ranked by how much each one
  affects the cost of future change;
- for each risk, the smallest change that would address it.

Findings only; edit nothing but this file. Units 026 and 027 are editing the
server and client in parallel; review what is committed (`git show HEAD:…`
if a file is mid-edit).

## Steps

- [x] Read the standards, design doc, README, every source and test file in `apps/vis`, the claims ledger's entry points.
- [x] Ran the checks: server 213 passed, basedpyright `all` clean; client `tsc` clean, vitest 54 passed (via `node_modules/.bin`, pnpm absent).
- [x] Counted the seams a change would cross (kind switches, numeric helpers, data-dependent tests).

## Decisions

- Judged against "a competent solo developer's weekend tool with tests", not a product: that is what the size (≈1,300 lines server, ≈900 client) warrants.
- Treated the design doc as the normative reference and the claims ledger as history, because that is how the README routes a reader.

## Final report

**Rating: 7.5 / 10.** Above common practice for a project this size on the things that decide the cost of change (one model, one protocol, typed and tested on both sides, docs that match the code). It loses points for one untested knot of client state, a few duplicated helpers, and no lint or one-command check.

**Strengths**, by how much each cuts the cost of future change:

1. **One model, one protocol, two seams.** `timeline.py` (`Hit`, `Cycle`, `repeat`) is the only abstraction; `guns.py`/`melee.py`/`casts.py` each expose `cycle(...) -> (Cycle, notes) | None`, and `queries._source` tries them in order. The JSONL registry (`types.Query`, `queries.registry`) is served identically by `http.py` and `__main__.py`, so any bug reproduces from the shell with `jq` and the client never sees a shape the CLI can't. A new damage source is a module plus one line in `_source`.
2. **The compiler writes the checklist.** `Kind` is closed on both sides (`types.Kind` with `assert_never` in `measures._words`; `protocol.AbilityKind` with `Record<AbilityKind, …>` in `selection.KNOBS`, `chart.widthCaption`). Adding `"item"` to the literal fails every site that must learn about it.
3. **Tests that a newcomer can run and read.** Synthetic trees in `conftest.py` make 200+ tests data-free; the real-data tests (`queries_test.DescribeRealData`: every live hero × every listed ability, at level 0 and 35) skip with a message naming `redo` when `data/` is absent, and are the patch-following safety net. Describe/it names say what, not how.
4. **Docs match the code.** `docs/dev/decisions.kb/vis-app.md` and `README.md` are accurate line for line against what is committed; every module docstring names the design section it implements. The claims ledger (`apps/vis/docs/dev/`) is optional reading.
5. **Modeling gaps are data, not comments.** Every simplification is a `note` line in the output (`casts.py` ranks them). Following a patch means fixing the number and watching the note change, not re-reading prose.

**Risks**, by how much each raises the cost of change; each with the smallest fix:

1. **`client/src/App.tsx` is the one untested module and holds the trickiest logic** (lines 655–674: the `periods`/`base`/`baseOf` JSON-key dance that remembers a cycle's period across horizon edits, and `useLines`' stale-answer guard). A second view will copy this. *Fix:* move `baseOf`, the period memory and `splitTimeline` into `selection.ts` (or a `timeline.ts`) with vitest cases; `App.tsx` keeps only JSX and hooks.
2. **Raw field names with `assert`, spread over four modules.** `casts.py` alone carries ~15 vdata property strings and fitted fallback lists (`_DURATIONS`, `_TICKS`); a renamed field after a patch is an `AssertionError` 500 with no body. The real-data smoke test catches it, but the module docstring's survey (99 of 184 bound …) is checked only as `> len(bound)/3` in `casts_test.DescribeRealData`, so the heuristic can drift silently. *Fix:* tighten that test to the survey's exact counts, so a patch fails it and points at the docstring to refresh.
3. **Five numeric-coercion helpers with five semantics**: `guns._num`/`_given`, `melee._num(value, *where)`, `casts._number` (regex, raises `BadRequest`), `boons._stat`, `queries._number`; and `num()` twice on the client (`selection.ts:129`, `chart.ts:181`). A newcomer must learn which to use. *Fix:* one `num(value, *where) -> float` next to `dig` in `deadlock/types.py`; one exported `num` in the client (`format.ts` or exported from `selection.ts`). `casts._number` and `queries._number` stay: they parse user input.
4. **No lint, no one-command check, no CI.** `App.tsx:896` disables an eslint rule nobody runs; the README lists four check commands across two toolchains; `bin/serve` needs `pnpm` for install though vite itself runs from `node_modules/.bin`. *Fix:* `apps/vis/bin/check` (≤50 lines bash) running both halves' checks; `ruff` in `pyproject.toml` dev group with defaults.
5. **Misplaced and vestigial pieces** that a reader must reason around: `Gun`/`gun_cycle` live in `timeline.py` but only `guns.py` uses them; `protocol.MeasureLine.label?` is optional "for older servers" that cannot exist (same repo, same process); `decisions.kb/vis-app.md` is still `status: proposed`. *Fix:* move `Gun` into `guns.py`; make `label` required; flip the status once the user rules.
6. **Documentation weight.** 40 files under `apps/vis/docs/dev/claims.kb/` for 2,200 lines of code, maintained by tools in a separate skills workspace; nothing fails when code changes without a claim. Low cost today because the README routes readers to the design doc first. *Fix:* none now; if the ledger goes stale, say so in `apps/vis/docs/dev/CLAUDE.md` rather than repair it.

Deviations: none; no code edited. Results live only in this file.
