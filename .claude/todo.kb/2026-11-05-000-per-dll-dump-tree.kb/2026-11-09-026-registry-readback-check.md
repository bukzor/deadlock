---
managed-by: Skill(llm-subtask)
status: done
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

- [x] Flag rule measured on the real readback (`trash/026/measure.py`)
- [x] `win32` native-call primitives; `dllscan.registry`; `document`, `__main__`
- [x] Real run (6860) of `dllscan registry` on `server`, `client` (`trash/026/run1/`)
- [x] Tests: `registry_check` 35 red on a stub, then green; `registry` 23 of 24 red on a
      stub; 33 hand mutants (`trash/026/mutants.py`, `-B`, pyc deleted) all killed
- [x] `data/dlls.check/registry.do`; acceptance run (logs `trash/026/redo-*.log`); docs

## Decisions

- **Flag rule, measured (6860):** non-`reference`: registry = queue + per-DLL flag (`gamedll`
  1975+4 already set, `clientdll` 2080+76). `reference`: queue minus `developmentonly defensive`
  (the sanitiser's), no per-DLL flag. One convar per DLL also carries `initial_setvalue
  performing_callbacks`: ignored as tier0 state, counted in the summary. Stricter than "flags
  minus the per-DLL flag": it asserts the flag was added.
- **Help compared too:** registry help = queue help, null as `""`; zero exceptions, one field.
- **Readback stops** at null (convars) or at what the invalid index 0xFFFF returns (commands:
  a shared tier0 `<unknown>` record). 018/hook_probe3's "494 vs 493" commands was that record.
- **No `ICvar` vtable hook:** the readback needs none. One placeholder stub for all slots
  (mode cell, `this` of the trap); `tier0` comes from the DLL's own load (`GetModuleHandleW`).
- **App systems hardcoded** (`APP_SYSTEMS`): `Source2ServerConfig001`, `Source2ClientConfig001`.
- **`.do` pipes** the readback into the check (no temp files); sources `winpy-facet.bash`
  (`lookup`, `require_loaded`, `closure`, `dllscan`) unchanged.

## Open Questions

- [ ] Out of scope, now stale: `icvar-hook.md` (6854 "494 against the queue's 493"; "5 others
      unexplained" flags) and the parent plan's `registry (later)` rows.
- [ ] Why one convar per DLL carries `initial_setvalue performing_callbacks` (`citadel_hero_release_vote_
      august_2025_debug_votes_cast_total`, `r_citadel_shadow_quality`): unproven why.

## Final report

Files: new `src/dllscan/registry{,_test}.py`, `src/deadlock/registry_check{,_test}.py`,
`data/dlls.check/registry.do`; edited `src/dllscan/{win32,document,__main__}.py`,
`docs/dev/cvar-dump.kb/validation.md` (registry readback as fact; Oracle stays `[!TODO]`).

API:
- `win32`: `module_handle(name) -> int`, `proc_address(module, name) -> int`,
  `alloc_executable(size) -> int`, `write(addr, data)`, `call(fn, *args: int | bytes) -> int`
  (SEH → `OSError`), `callback(fn: Callable[[int, int], int]) -> int`.
- `document.RegistryDocument`: `module, stopped_by: str | None, convars: Sequence[ConVar],
  concommands: Sequence[ConCommand]`.
- `registry`: `read_back(dll, dirs) -> RegistryDocument`; `APP_SYSTEMS`; pure `block(base)`,
  `Placeholders`, `convar_record(mem, addr)`, `command_record(mem, addr)`, `walk(get)`.
  CLI `bin/winpy dllscan registry DLL [DIR ...]`.
- `deadlock.registry_check`: `check(registry, convars, concommands) -> list[str]`,
  `convar_mismatches`, `command_mismatches`, `PER_DLL_FLAG`, `SANITISED`, `STATE`,
  `zero_value`, `is_registry_document`; CLI `... | python -m deadlock.registry_check CV.json CC.json`.

Acceptance (6860): `redo data/dlls.check/registry` exit 0, 28 s:

    server.dll convars: queue 2008, registry 2003, once 1999 (reference 19), all match
    server.dll concommands: queue 493, registry 493, once 493, all match
    client.dll convars: queue 2289, registry 2234, once 2226 (reference 69), all match
    client.dll concommands: queue 428, registry 428, once 428, all match

= 019's table (default/version 1980 and 2157 plain, + 19/69 by the reference rule).
Mutants through redo: `values` int32 size 16 → fails ('default' mismatches); check's
reference `version` → fails ('version' on reference names). Restored, check passes again.
Plain `redo`: rebuilt every `file` atom (`lookup` depends on `document.py`) and load-time atom
(scanner glob); second `redo` runs only `all`, `gamedata.list`, `date.txt`. All 606 data files
byte-identical to the before snapshot; `git diff data/` empty. Readback byte-identical across runs.
`pytest src` and `pyright` clean; 33 hand mutants killed. Deviations: help compared; stricter
flag rule (above); `stopped_by` field.
