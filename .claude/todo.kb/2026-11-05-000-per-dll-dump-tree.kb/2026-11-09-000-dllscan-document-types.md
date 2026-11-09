---
managed-by: Skill(llm-subtask)
status: done
---

# `dllscan.document`: the facet documents' `TypedDict`s

**Priority:** wave 1 of the scanner core
**Complexity:** low: types only, no runtime behaviour
**Context:** parent plan <https:../2026-11-05-000-per-dll-dump-tree.md> (`src/dllscan/`
table, `document` row); `docs/dev/convar-dump.kb/output-views.md`,
`dll-coverage.md`, `registration-flow.md`

## Problem Statement

Write `src/dllscan/document.py`: one `TypedDict` per first-wave facet document.
Both the Windows-side scanner and the WSL `deadlock.*` aggregators import it,
so pyright checks the documents on both sides of the process boundary.

- `file`: size, sha256.
- `load`: a union discriminated on outcome: `ok` (+ the modules the load pulled
  in, sorted basenames), `failed` (+ error), `excluded` (+ reason).
- `convars`: `{module, convars: [...]}` in queue order; entry `{name, help,
  flags, type, default, min, max}`. Flags are names, type is the `EConVarType`
  name, and values are decoded by type, or hex when they don't decode.
- `concommands`: `{module, concommands: [...]}`; entry `{name, help, flags}`.
- No `build` field, no addresses, no queue index (position is the index).

Constraints: stdlib `typing` only, 3.12-compatible, ≤300 lines. Scope is
`document.py` (+ a test only if it has behaviour). Create `__init__.py` empty
if missing. Do not touch `pyproject.toml`, `memory.py`, `flags.py`, git, the
plan, or the docs. Finish with pyright clean.

## Implementation Steps

- [x] Write `src/dllscan/document.py` (108 lines)
- [x] Create an empty `src/dllscan/__init__.py` (it was missing)
- [x] `./bin/shell pyright src/dllscan/document.py`: 0 errors
- [x] Probe the types with pyright (`trash/document-check/probe.py`): a valid
      `ConVarsDocument` passes; an entry missing `min` and `{"outcome": "ok",
      "error": ...}` are rejected; `match d["outcome"]` narrows each arm
- [x] No `document_test.py`: nothing runs, so pyright is the test

## Decisions

- **`null`, never a missing key.** Every entry has the same keys, so a value
  that appears is one changed line in a pretty-printed diff, not an inserted
  one; the TSV gets a fixed set of columns; readers never need `.get`.
- **`default` can be `null` too.** The creation struct has has-default as well
  as has-min and has-max bytes. `null` means that byte is 0.
- **`type: str`, not a `Literal`.** Unknown values are written `type_<n>`, as
  `hook_probe3.py` does, and the name table belongs to `dllscan.values`.
- **`ConVarValue = bool | int | float | str | Sequence[float]`.** A color is
  4 ints and a vector or qangle is floats; hex is a lowercase `str`.
- **`Sequence`, not `list`.** House style: read-only data gets covariant types.
  Producers can pass lists.
- **`module` is the basename from `dlls.list`** (`server.dll`), the same form
  as `load.modules`.
- **No general `JsonValue` alias.** Nothing here needs one.

## Open Questions

- [ ] A `str` value is ambiguous when `type == "string"`: the real value or a
      hex fallback? Either `values` guarantees that strings always decode, or
      the fallback gets its own shape (e.g. `{"hex": ...}`).
- [ ] When a has-X byte is 0, `null` drops any non-zero value bytes. Does
      "lossless" cover them?
- [ ] `module` as `server.dll` or as `server`? `entries`, `__main__` and the
      aggregators must all use the same form.
- [ ] Windows reports some names in upper case (`KERNEL32.DLL`): `win32`/`load`
      should lowercase before sorting, or diffs will churn.

## Notes

Environment: a sub-agent's shell inherits `DIRENV_DIR`/`DIRENV_DIFF` without
direnv's PATH entries, so `direnv export` is a no-op and `./bin/shell pyright`
fails with "command not found". Workaround:
`env -u DIRENV_DIR -u DIRENV_DIFF -u DIRENV_WATCHES ./bin/shell pyright …`.
