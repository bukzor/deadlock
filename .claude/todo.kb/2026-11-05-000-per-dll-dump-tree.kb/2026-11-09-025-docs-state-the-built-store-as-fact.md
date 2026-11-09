---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/CLAUDE.md
  - docs/dev/cvar-dump.kb/CLAUDE.md
  - docs/dev/decisions.kb/CLAUDE.md
  - docs/dev/decisions.kb/reuse-existing-parsers.md
---

# Docs: state the built store as fact, and record its decisions

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the step "Docs: drop
each `[!TODO]` callout as it lands …")

## Problem Statement

The store is built (the plan's ticked steps; the code under `src/dllscan/`,
`src/deadlock/` and `data/dlls*/`). `docs/dev/cvar-dump.kb/` still says much
of it in the future tense. Bring the docs to the current truth:

- **`[!TODO]` callouts:** check each one under `cvar-dump.kb/` against the
  code. If it is built, drop the callout so the sentence stands as fact. If it
  is built differently, rewrite the sentence to what was built. Leave two for
  their siblings: the registry readback (`validation.md`, a later unit) and
  the import closure (`dll-coverage.md`, 024 runs concurrently).
- **`capture-approach.md`:** close its `[!QUESTION]` (the values decode, 019;
  the owner-check exception is the per-kind ref check, 013). Rewrite it as the
  answer, as `docs/dev/CLAUDE.md` and the llm-kb decision-point rule say.
- **`decisions.kb/`:** add two decisions, in that collection's own form.
  1. The tool choice. The project owns a scanner here, which departs from
     `reuse-existing-parsers.md`, and says why, so a later agent doesn't
     "fix" it. Then drop the matching sentence in `cvar-dump.kb/CLAUDE.md`.
  2. The lossless per-DLL store with atomic facets: one process per
     (facet, DLL), and the documents as the source that views adapt.
- **Small fixes:**
  - `registration-flow.md`'s title says "convar" but covers both kinds.
    Use "cvar" (022's Open Questions).
  - Two links to `bin/shell` don't resolve from their files:
    `docs/dev/environment.kb/toolchain.md` and handoff 001. Write each as a
    mention, not a link (llm-kb's link convention), unless a link is what
    the sentence needs.

Don't change the design. Leave `[!QUESTION]`s other than `capture-approach.md`'s
as they are.

**Check:** `~/.claude/skills/llm-kb/bin/llm.kb-validate-links` over
`docs/dev/` and `.claude/todo.kb/` reports no broken links.

**Scope:** `docs/dev/cvar-dump.kb/**` (except `validation.md`'s registry callout
and `dll-coverage.md`'s import-closure text), `docs/dev/decisions.kb/` (the two
new files), `docs/dev/environment.kb/toolchain.md`, and handoff 001's one link.
023 and 024 edit `bin/` and `data/dlls/*/default.json.do` concurrently; none of
those are yours.

## Steps

- [x] Check each `[!TODO]` under `cvar-dump.kb/` against the code; drop or rewrite
- [x] `capture-approach.md` as the answer; its `.kb/CLAUDE.md` to match
- [x] Two decisions in `decisions.kb/`; drop the sentence in `cvar-dump.kb/CLAUDE.md`
- [x] Small fixes: `registration-flow.md` title, two `bin/shell` mentions
- [x] Check: links, `llm.kb-validate`, llm-kb self-audits

## Decisions

- Built differently, rewritten: validation's ref check is per kind (013); a
  misfit entry hides its queue instead of failing (`reglist.walk` returns
  None), so Shape says so and names Coverage/Oracle as the backstop.
  `convars.tsv` has a `version` column. All four facet TSVs are committed.
- `validation.md`: Shape/Anchors/Coverage stated as fact; Oracle and Registry
  readback moved, words unchanged, into one `[!TODO]` (both unbuilt). That
  callout is 026's to drop.
- `output-views.md`: "No input but the DLL…" became "No atom reads another
  DLL's document": still true once 024 adds the import closure.
- Updated to 6860 from the committed TSVs: `phonon4` also fails to load; 8 (not
  6) tier0-loading DLLs yield no queue (+`netgraph_subtool`,
  `soundviewer_subtool`); 30 + 30 queues, 6223 + 1418 declarations.
- `[!TODO]` kept for the later facets (`pe`, `interfaces`, …): unbuilt.

## Open Questions

- `docs/dev/CLAUDE.md` enumerates decisions by name (llm-kb says don't); out
  of scope, so the two new ones aren't listed. Suggest dropping the list.

## Final report

Files touched: `docs/dev/cvar-dump.kb/{CLAUDE.md, capture-approach.md,
capture-approach.kb/CLAUDE.md, capture-approach.kb/queue-shape-scan.md,
dll-coverage.md, output-views.md, registration-flow.md, validation.md,
windows-python-host.md}`, `docs/dev/environment.kb/toolchain.md`, handoff 001
(one mention). New: `docs/dev/decisions.kb/own-the-dll-scanner.md`,
`docs/dev/decisions.kb/lossless-per-dll-store-with-atomic-facets.md`.

Checks: `llm.kb-validate docs/dev`: 36 files, 0 errors.
`llm.kb-validate-links docs/dev/ .claude/todo.kb/`: 2 remaining, both
`bin/shell` with a `./` prefix, outside my scope: this brief's Problem Statement (line
41) and handoff 022's Final report (line 78). Write them as `bin/shell` to
clear the check.

Deviation: `dll-coverage.md`'s import-closure `[!QUESTION]` untouched (024);
`deadlock.dll_load.EXCLUDED`'s docstring already answers it (unit 007).
