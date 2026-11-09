---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-09-001-dllscan-skeleton-and-memory.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-001-dllscan-skeleton-and-memory.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-003-dllscan-image-layout.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/cvar-dump.kb/windows-python-host.md
  - docs/dev/cvar-dump.kb/dll-coverage.md
  - ~/.claude/must-read.kb/before/writing-bash-scripts.md
---

# `dllscan.win32` and `bin/winpy`: the Windows side of the boundary

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Wave 3, beside
`reglist`; the `win32` row and "`bin/winpy`: the process boundary")

## Problem Statement

Two pieces, built and verified together, because each is only testable
through the other:

**`src/dllscan/win32.py`**, the only Windows-only module (ctypes, stdlib):
- add the DLL directories (`os.add_dll_directory`), taken as arguments in
  Windows form: both bin dirs and the DLL's own dir. `dllscan` never
  computes paths; the WSL side (`deadlock.paths`) passes them in.
- `LoadLibraryExW` → base address; failure raises with the Win32 error.
- the loaded-module list: basenames, **lowercased**, sorted. This feeds
  `document.LoadOk.modules`, so diffs must not churn on Windows' casing.
- `ReadProcessMemory` on our own process, exposed as a `memory.Read`: it
  returns `None` on failure and never raises or crashes.
- `hard_exit(code)`: flush stdout and stderr, then `TerminateProcess`
  (skips DLL detach and static destructors, which can hang).

It must import cleanly on Linux: pytest runs `--doctest-modules` over
`src/`, and pyright checks it at `pythonVersion = 3.12`. Find a structure
where pyright still type-checks the ctypes code on Linux. A
`sys.platform` guard alone makes pyright treat it as unreachable, so check
that it really is analyzed. Unit tests only cover what is platform-neutral.

**`bin/winpy`** (bash, ≤50 lines, the house template): `bin/winpy MODULE
ARGS…` runs `python.exe -m MODULE ARGS…` with `src/` on `PYTHONPATH` (the
Windows form of the path, through `WSLENV`) and stdin from `/dev/null`. Its
cwd is `trash/winpy/`, which catches `*.mdmp` files. It runs under
`timeout` and passes the exit status through. If `python.exe` is missing, it
fails loudly. Verify whether Windows Python accepts a `\\wsl.localhost\…`
entry on `PYTHONPATH`. If it doesn't, find what works and record it.

**Verification on the real install** (no committed test): with a throwaway
driver in `trash/winpy/` run through `bin/winpy`:
- load `server.dll` and `client.dll`, then run `image.read_image` over
  `ReadProcessMemory` and compare against the on-disk header check in
  003's Final report;
- print the module list;
- show that an unreadable address returns `None`;
- show that `hard_exit` returns the code under `timeout`.

Never load `helpsystem`, `assetpreview`, `propertyeditor` or
`toolframework2`: they hang `LoadLibrary` with an unkillable process
(build 6851). Get the game dir from `python -m deadlock.paths game_dir`,
then convert it with `wslpath -w`.

**Scope:** `src/dllscan/win32.py`, `src/dllscan/win32_test.py` (if anything
is platform-neutral), `bin/winpy`. `__main__` is the next unit: don't write it.

## Steps
- [x] `win32.py` (injected type errors reported: analyzed on Linux; doctest driven red by 2 mutants); `bin/winpy` (shellcheck clean); real checks via `trash/winpy/{win32_check,sleep_check}.py`; `pytest src/dllscan` 61 passed (sibling `reglist`, in progress, hangs: excluded), `pyright` 0 errors

## Decisions
- No Windows-only stub names (`ctypes.WinDLL`, `os.add_dll_directory`): lazy `ctypes.CDLL("kernel32")`, `AddDllDirectory` called directly (all `os.add_dll_directory` does); signatures in a `_Kernel32` Protocol, double `cast` (ctypes calls return `Any`); `get_last_error` via `getattr`. `LoadLibraryExW` flags as `ctypes.CDLL`'s. Errors carry the numeric code, not `FormatMessage` text (locale-dependent). No `win32_test.py`: the one neutral behavior is a doctest. `winpy` also sets `PYTHONUTF8=1` (else stdout is cp1252).

## Open Questions
- [ ] For `__main__`: `module_names()` includes Python's own 27 modules (`python314.dll`, `_ctypes.pyd`…), churning on a Python upgrade: record `after - before` the load. Windows stdout writes `\r\n`: `sys.stdout.reconfigure(newline="\n")`.

## Final report
Files (new): `src/dllscan/win32.py`, `bin/winpy`. API (Windows-form paths in): `class Win32Error(Exception)` (`.function: str`, `.code: int`, args `(function, code, arg)`); `add_dll_directories(dirs: Iterable[str]) -> None`; `load_library(path: str) -> int` (base; `Win32Error("LoadLibraryExW", 126, path)` if not found); `module_names() -> list[str]` (lowercased basenames, sorted); `read(addr: int, n: int) -> bytes | None` (a `memory.Read`); `hard_exit(code: int) -> NoReturn`. `bin/winpy MODULE ARGS…`: status passed through (124 timeout, 127 no `python.exe`, 2 no MODULE); `timeout ${WINPY_TIMEOUT:-60}`. `PYTHONPATH` via `WSLENV` `/p` arrives as `\\wsl.localhost\Alpine\…\src`, and Windows Python imports from it. Real install (6860): `server.dll`, `client.dll` load (~0.25 s); `read_image` over `read` equals the on-disk layout (`server` span 0x4985000, 5 sections, as 003). 52 modules, lowercase, sorted. `read` → None at 0, 0x10, 0x7fffffff0000, 2**47+0x1000, -1, 2**64-4. `hard_exit(7)` → 7; 30 s sleep under `WINPY_TIMEOUT=3` → 124, no `python.exe` left; stdin reads `''`.
