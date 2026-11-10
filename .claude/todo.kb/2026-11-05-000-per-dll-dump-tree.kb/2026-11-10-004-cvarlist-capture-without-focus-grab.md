---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-10-003-cvarlist-capture-tracked-inputs.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-10-000-cvarlist-capture.md
  - docs/dev/game-runtime.kb/cvarlist-capture.md
  - bin/cvarlist-capture
---

# Captures that don't take the user's focus

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the `cvarlist` oracle)

## Problem Statement

A capture's game window sometimes takes keyboard focus from whatever the
user is doing, and sometimes doesn't. The goal: it never takes focus. A
visible flash is acceptable; no flash at all is a bonus. This is a
low-priority polish task. Time-box it to about 30 minutes of experiments.
If nothing works cleanly, report what was tried and change nothing.

The working guess about why it's intermittent is Windows' foreground rules.
A new process may take the foreground only when the user hasn't given any
input for `ForegroundLockTimeout` (default 200 s), or in a few other cases.
Otherwise Windows refuses and flashes the taskbar button. Confirm or refute
this if you can: read the registry value, and try a launch during idle and
one during input.

Try, cheapest first, and keep the first that works:
1. Start minimized without activation: a `STARTUPINFO` show state, e.g.
   PowerShell `Start-Process -WindowStyle Minimized`, or
   `SW_SHOWMINNOACTIVE`. Windows applies it to the program's first
   `ShowWindow` call. Find out whether Source 2 then forces itself to the
   front.
2. Server side: start its console hidden.
3. Only if 1 fails for the client: an off-screen or hidden desktop
   (`CreateDesktop`), if DirectX starts there. Don't switch the client to
   the empty render backend: the oracle would lose `rendersystemdx11`'s
   coverage.

Whatever you change, the launcher must still find and kill its own process
by the log-name marker, refuse to launch while `deadlock.exe` runs, and stay
within 50 lines of bash.

**How to test without the user:** you can't see the screen. Use
`GetForegroundWindow` (via PowerShell and `user32`) before, during and after
a launch to read which process owns the foreground, and record it.

**Acceptance (6860):** `redo data/dlls.check/cvarlist` passes with the
change in place. Show the foreground-window readings for each launch.

**Also:** `data/dlls.check/cvarlist.do`'s comment still calls each log "a
fresh launch of the game". Since 003, a capture reruns only when its inputs
change. Fix the comment, whatever the experiments' outcome.

**Scope:** `bin/cvarlist-capture`, `docs/dev/game-runtime.kb/cvarlist-capture.md`
(a sentence on focus), the comment in `data/dlls.check/cvarlist.do`, and a probe
under `docs/dev/probes/` if the KB cites it. Captures rerun only when their
inputs change (003): to force a launch, delete `data/cvarlist/<side>.log` first.

## Steps

- [x] Foreground watcher (`docs/dev/probes/foreground_watch.ps1`); registry read
- [x] Baseline: direct launch, each side
- [x] 1: `cmd /c start /min` (server ok; client still takes the foreground)
- [x] 3: hidden desktop (`CreateDesktop` + `lpDesktop`): both sides ok
- [x] Wire into `bin/cvarlist-capture`; KB Focus section; `.do` comment
- [x] Acceptance `redo data/dlls.check/cvarlist`; timeout-kill path

## Decisions

- Hidden desktop for both sides, not `start /min` for the server plus a desktop
  for the client: one mechanism, and it also removes the flash.
- The CreateProcess call lives in `bin/on-hidden-desktop.ps1` (C# via
  `Add-Type`): it can't fit in 50 lines of bash. `.cmd` still records the game's
  own command line, which reproduces the listing (it just may take focus).

## Open Questions

- Untested: a launch while another app (not this terminal) is in front.

## Final report

Files: `bin/cvarlist-capture` (50 lines; launch goes through the helper),
`bin/on-hidden-desktop.ps1` (new, 34 lines: `powershell.exe -File
on-hidden-desktop.ps1 EXE ARGS...`, run from EXE's dir; exits with EXE's code),
`docs/dev/game-runtime.kb/cvarlist-capture.md` (Procedure line, new Focus
section), `docs/dev/probes/foreground_watch.ps1` (new, cited),
`data/dlls.check/cvarlist.do` (comment fixed).

Hypothesis refuted: `ForegroundLockTimeout` = 200000 (default), yet with the
user idle < 4 s the direct launch took focus (server 1/1, client 1/2) or not
(client 1/2). Readings (`trash/focus/*.fg`, fg owner on each change):
- base-server: Terminal -> deadlock console 13:14:04.8 -> explorer -> Terminal
- base-client: Terminal throughout; base-client2: Terminal -> deadlock 'Deadlock'
  (shown) 13:16:32.9 -> Terminal
- min-server: Terminal throughout; min-client: Terminal throughout;
  min-client2: Terminal -> deadlock (`:min`, still foreground) -> Terminal
- desk-server, desk-client, acceptance (server + client): Terminal throughout

Checks: acceptance `redo data/dlls.check/cvarlist` relaunched both sides and
passed (server 1765, client 2513 with `rendersystemdx11.dll` loaded); listings
identical to direct launches; rerun launches nothing. `CVARLIST_TIMEOUT=3`
client: killed its own PID by marker, failed, no stray process or log.
Refusal-while-running code unchanged. shellcheck: only SC2329 (info, `onerror`
via trap; pre-existing).

Deviation: new `bin/on-hidden-desktop.ps1`, outside the brief's file list.
