---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-09-006-dllscan-entries-names-help-flags.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-000-dllscan-document-types.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-003-dllscan-image-layout.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-004-dllscan-reglist.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-005-dllscan-win32-and-winpy.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-006-dllscan-entries-names-help-flags.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/cvar-dump.kb/validation.md
  - docs/dev/cvar-dump.kb/dll-coverage.md
---

# `dllscan.__main__`: `load`, `concommands`, `strides`, and the first real run

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Wave 5; the
`__main__` row, and the steps "Time `find_heads`" and "Re-run on 6860")

## Problem Statement

The scanner's CLI, run as `bin/winpy dllscan <subcommand> …`, one process per
(facet, DLL). Each subcommand prints one document (`document` types) to stdout.

- **`load DLL`**: add the DLL directories, take the module list before and
  after `load_library`, and record `after - before`, sorted. That list is
  only what this DLL pulled in; it leaves out Python's own modules, which
  change whenever Python is upgraded. Print `LoadOk`. A `Win32Error` from the
  load is data, not a crash: print `LoadFailed` (the error as a stable string,
  function + numeric code) and exit 0. `excluded` is written WSL-side, never
  here.
- **`concommands DLL`**: load, `read_image`, `find_queues` at the pinned
  stride, then decode every entry with `entries.decode_concommand`.
  - No queue → an empty list. Not every DLL has one.
  - More than one queue → `ShapeError`.
  - `module` is the lowercased DLL basename, the same form as `load`'s
    module list.
- **`strides DLL`**: `learn_strides`, then compare with `STRIDES`. Exit
  non-zero, with a message, if they moved. Label the learned strides by the
  anchors in `validation.md` if that's cheap; otherwise leave them unlabelled
  and record the gap in Open Questions.
- **No `convars` subcommand yet.** It waits for the value decode. Do not
  print placeholder values.
- **How the DLL path and directories are passed** (argument shape) is yours
  to choose. The WSL `.do` files will call this, so report the exact
  invocation.
- **Output:** deterministic and byte-identical across runs. `\n` line endings
  (`sys.stdout.reconfigure(newline="\n")`; Windows writes `\r\n` otherwise).
  UTF-8. Choose and justify the JSON formatting.
- **Errors:** any exception → message on stderr, `hard_exit(1)`. Success also
  ends through `hard_exit(0)`, after a flush.

Keep the document assembly pure (over `Memory` + `Image`) so WSL pytest covers
it with fakes. Only the glue touches `win32`. Where that pure code lives
(inside `__main__` or a small module beside it) is yours; report it.

**Real-install run** (6860, through `bin/winpy`). Record every result in the
Final report, labelled with the build:
1. `load`, `concommands` and `strides` on `server.dll`, `client.dll` and
   `engine2.dll`. Concommand counts vs 6854's `server` count (493).
2. Convar queue sizes from a throwaway driver in `trash/`: `find_queues` at
   stride 160, entry count only. Compare with 6854's `server` count (2008).
   `validation.md`'s coverage check says `engine2`, `client` and `server`
   each yield both queues.
3. Run `concommands server.dll` twice and confirm the two outputs are
   byte-identical.
4. Time `find_queues` on `server.dll` at each stride, against the ~0.2 s
   per-process overhead. Then answer the plan's Open Question: keep
   `convars` and `concommands` as two facets, or merge them into one
   `reglists` facet? Give the numbers.

**Scope:** `src/dllscan/__main__.py`, its test, a pure helper module and its
test if you split one out, and `trash/` for drivers.

## Steps

- [x] `facets_test.py` against a stub: 13 red
- [x] `facets.py`: green; 17 mutants (`trash/facets-mutants/run.py`, `-B`, pyc
      deleted), all killed, every test red under at least one
- [x] `__main__.py` (glue); `pytest src/dllscan` 131 passed; `pyright src/dllscan` 0
- [x] Real run (6860), outputs in `trash/main008/`; drivers
      `trash/winpy/main008_{queues,split}.py`, `trash/main008/writable_total.py`

## Decisions

- **Pure code in `dllscan.facets`**, not `__main__`: `__main__` stays glue
  (argparse, `win32`, exit), `facets_test` drives the rest over `reglist_test.Fake`
  (imported, not moved: moving it would edit `reglist_test.py`, out of scope).
- **Arguments:** `dllscan SUBCOMMAND DLL [DIR ...]`, all Windows form; the DIRs
  go to `add_dll_directories` (the DLL's own dir needs no DIR:
  `LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR`). Positional: the `.do` builds one argv.
- **`LoadFailed.error` = `"<function>: <code>"`** (`LoadLibraryExW: 126`): no
  path (varies by install), no message text (varies by locale).
- **JSON:** `indent=2`, `ensure_ascii=False`, declared key order (no
  `sort_keys`), trailing `\n`. One value per line, so a changed value is one
  diff line (000's rule); UTF-8 help text stays readable. stdout is
  `reconfigure(encoding="utf-8", newline="\n")`, independent of `PYTHONUTF8`.
- **`strides` output:** `[{stride, kind, entries}]` in `learn_strides` (head
  address) order. `kind` = the `STRIDES` key the queue's `ANCHORS` names, else
  null. `ShapeError` (exit 1, no output) unless the learned strides, as a
  multiset, equal `STRIDES`, each labelled one has its kind's stride, and no
  queue holds anchors of both kinds. Unlabelled queues are allowed, so the
  command also works on DLLs without the server anchors (client, engine2).
- **Errors:** argparse misuse exits 2 the usual way (before any load); every
  other exception: traceback on stderr, `hard_exit(1)`.

## Open Questions

- [ ] Anchors label by name only; their flags (validation.md "with the right
      flags") are unchecked. On 6860 they match: `bot_kick_all` cheat
      client_can_execute, `citadel_bot_kick` developmentonly defensive. Belongs
      to the `data/dlls.check/strides` target.
- [ ] `document.LoadOk`'s docstring still says "every module the process
      holds"; it is now the modules the load added (out of scope here).
- [ ] A missing file and a missing dependency both give `LoadLibraryExW: 126`;
      the `.do` guard (basename in `dlls.list`) must keep the first from
      happening.
- [ ] `client`'s command queue labels `null`: no anchor is a client command.

## Final report

Files (new): `src/dllscan/{__main__,facets,facets_test}.py` (90/90/132 lines).

API, `dllscan.facets`: `ANCHORS: Mapping[str, str]` (name → `STRIDES` key);
`class LearnedStride(TypedDict): stride: int; kind: str | None; entries: int`;
`load_ok(before: Iterable[str], after: Iterable[str]) -> LoadOk`;
`load_failed(error: Win32Error) -> LoadFailed`;
`concommands(mem, image, dll: str) -> ConCommandsDocument` (`module` =
`ntpath.basename(dll).lower()`; no queue → `[]`; two → `ShapeError`);
`strides(mem, image) -> list[LearnedStride]` (raises as in Decisions);
`dumps(document: object) -> str`. A later `convars` reuses `dumps` and the
`concommands` pattern.

Invocation (`.do`): `bin/winpy dllscan {load|concommands|strides}
"$(wslpath -w "$dll")" "$(wslpath -w "$game/bin/win64")"
"$(wslpath -w "$game/citadel/bin/win64")" >"$3"`. Exit 0 with one document;
1 with a traceback; 124 timeout.

Real install, build 6860:
- `load`, all ok: server adds 5 modules (`server shell32 steam_api64 tier0
  winmm`), client 24, engine2 7. `vfx_dx11` → `LoadFailed`
  `LoadLibraryExW: 126`, exit 0 (as on 6851).
- `concommands`: server 493 (= 6854), client 428 (6848: 427), engine2 220
  (6848: 220); names unique within each; no `\r` in output.
- Convar queues (`find_queues` 160): server 2008 (= 6854), client 2289 (6848:
  2288), engine2 423. Each of the three yields both queues (coverage check).
- `strides`: all three exit 0 with 160/64. Labels: server convars +
  concommands; client convars + null; engine2 null + null.
- `concommands server.dll` ×3: byte-identical (sha256 `231ba05b…`).
- Timing, server: `find_queues` 0.57–0.66 s per stride, of which the
  stride-independent candidate search is 0.61 s and the walks 0.04 s (64) /
  0.11 s (160); client 0.54–0.71 s, engine2 0.11–0.14 s. `learn_strides`
  2.9 s. Process overhead measured here is larger than the plan's 0.2 s:
  bare `bin/winpy timeit pass` 0.59 s, `dllscan load server.dll` 0.9–1.0 s
  end to end (imports over `\\wsl.localhost`; a sibling ran concurrently).
- **`reglists` question: keep two facets.** Total writable bytes over all 97
  DLLs is 130.6 MB, so the second search costs ~5 s CPU per full build at
  server's 0.039 s/MB (<1 s wall at `-j8`). The second process costs ~90 s CPU
  (97 × ~0.9 s), but every load-time facet pays that by design; merging these
  two alone is the wrong lever. If the scan ever matters, `reglist` can share
  `_candidates` across strides within one call.

Deviations: none from the brief. Checks: `pytest src/dllscan` 131 passed,
`pyright src/dllscan` 0 errors.
