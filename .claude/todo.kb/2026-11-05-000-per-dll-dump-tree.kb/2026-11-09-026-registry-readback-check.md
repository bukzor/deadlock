---
managed-by: Skill(llm-subtask)
status: open
blocked-by:
  - 2026-11-09-024-load-time-atoms-depend-on-import-closure.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-018-convar-value-layout-fit.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-019-dllscan-convar-decode.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-020-convars-atom-aggregate-check.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-024-load-time-atoms-depend-on-import-closure.md
  - docs/dev/cvar-dump.kb/validation.md
  - docs/dev/cvar-dump.kb/capture-approach.kb/icvar-hook.md
  - docs/dev/probes/hook_probe3.py
---

# The registry readback check: `dllscan registry` + `deadlock.registry_check`

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the step "On-demand
checks", the `registry` rows of its tables, and the success criterion "Registry
readback check passes for `server` and `client`")

## Problem Statement

The queue scan decodes values by our reading of the layout. Only tier0's own
registry checks that reading against the engine. `hook_probe3.py` and 018's
`trash/valuefit/` already read it back: hook `ICvar`, run the DLL's `Init`,
read what tier0 registered. Promote that to built code:

- **`dllscan.registry`** (stdlib only, pure except through `win32`, like the
  rest of `dllscan`), and a CLI subcommand `bin/winpy dllscan registry DLL
  [DIR ...]` that prints the registry document as JSON. Add its `TypedDict`
  to `dllscan.document`. Values decode through `values`, as 019's pass check
  did on both sides.
- **`deadlock.registry_check`**: the registry document against the DLL's
  `convars` and `concommands` documents. Every queue entry's name is in the
  registry. Each name declared once must match on: type, flags minus the
  per-DLL flag, default, min, max and version (convars), and flags
  (commands). 018's finding is the rule for a `reference` declaration
  (has-default 0): its document default is `null` and the registry holds the
  type's zero value (version -1). Assert that rule; don't skip those entries.
  Print a summary of counts; any mismatch fails with the names.
- **`data/dlls.check/registry.do`** for `server` and `client`. It runs on
  demand: it is not a dependency of `all.do`. It depends on exactly what it
  reads, like its sibling checks.
- **Docs:** drop the `[!TODO]` on the registry readback in
  `cvar-dump.kb/validation.md`, if one is left, and point the sentence at
  the target. `hook_probe3.py` stays: probes are archived evidence
  (`docs/dev/probes/CLAUDE.md`).

The `cvarlist` oracle is not part of this unit.

**Acceptance (6860):** `redo data/dlls.check/registry` exits 0 and prints the
counts, which agree with 019's pass table. A mutant in `values` or in the
check's comparison makes it fail (`-B`, delete the `.pyc`). `pytest src` and
`pyright` are clean. A plain `redo` afterwards is a no-op apart from the
atoms the new `dllscan` module legitimately rebuilds, and `git diff data/` is
empty.

**Scope:** new `src/dllscan/registry{,_test}.py`, `src/dllscan/{document,__main__}.py`
(and `win32.py` if the hook needs a primitive), new
`src/deadlock/registry_check{,_test}.py`, new `data/dlls.check/registry.do`,
`docs/dev/cvar-dump.kb/validation.md`.

## Steps

## Decisions

## Open Questions

## Final report
