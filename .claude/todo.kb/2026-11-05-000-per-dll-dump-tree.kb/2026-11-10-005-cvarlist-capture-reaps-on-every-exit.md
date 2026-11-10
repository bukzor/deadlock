---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-10-004-cvarlist-capture-without-focus-grab.md
  - ~/.claude/must-read.kb/before/writing-bash-scripts.md
  - bin/cvarlist-capture
  - bin/on-hidden-desktop.ps1
---

# `bin/cvarlist-capture` reaps its own launch on every exit

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the `cvarlist` oracle)

## Problem Statement

Since 004, the game runs on a hidden desktop, so a stuck launch is
invisible. The launcher kills its own `deadlock.exe` (by the log-name
marker) only on the normal path, after `timeout` returns. On an interrupt
or an error exit the WSL side exits and the Windows processes keep
running: `timeout`, and so Ctrl-C, ends only the interop shim. A
`deadlock.exe` that hangs then stays running, out of sight.

Run the marker kill on every exit: success, error, timeout, and an
interrupt (`INT`, `TERM`) during the launch. Keep it to processes whose
command line carries this launch's marker, and keep the other behaviour
unchanged. Stay at or under 50 lines.

**Acceptance (6860):**
- A normal capture still passes: `redo data/dlls.check/cvarlist` after
  deleting `data/cvarlist/client.log`.
- An interrupt mid-launch leaves no `deadlock.exe` running: send `INT` to
  the launcher a second or two in, then check `tasklist.exe`.
- The `CVARLIST_TIMEOUT=3` path still kills its own launch and fails.
- Afterwards, only `Default` is listed among `WinSta0`'s desktops
  (`trash/desk/enum.ps1` enumerates them).

**Scope:** `bin/cvarlist-capture`, and a sentence in
`docs/dev/game-runtime.kb/cvarlist-capture.md` if it describes the kill.

## Steps

- [x] `reap` (marker roots, `/T`) on `EXIT`; `INT`/`TERM` exit through it; launch under `wait`
- [x] Doc: Stuck launch bullet
- [x] Acceptance: normal, `INT` at ~2 s, `CVARLIST_TIMEOUT=3`, desktops

## Decisions

- Match any process whose command line carries the marker, not only
  `deadlock.exe`: the hidden-desktop helper carries it too, so an interrupt
  before the game starts kills the helper and no game ever launches. Kill only
  the roots among the matches (`ParentProcessId -notin`), `/T` taking the
  rest: a second `taskkill` on an already-killed child would fail the trap.
  The query excludes its own `$PID` (its command line holds the marker too).
- Launch as `... & wait $!`: `wait` returns on a trapped signal at once; a
  foreground `timeout` would defer the trap until the launch ended (up to
  180 s). `INT`/`TERM` traps `exit 130`/`143`, which runs the `EXIT` trap.
- `trap reap EXIT` armed just before the launch (an empty `$log` would match
  every process), cleared after the explicit `reap` that must precede `mv`,
  so a normal run queries once.
- 50 lines: the refusal's `exit 1` joined its `echo` line, as usage does.

## Open Questions

- `taskkill /F` returns before a 545 MB client finishes tearing down:
  `tasklist` right after an `INT` at 5 s still listed it; gone a moment
  later. An immediate relaunch could briefly refuse.
- An interrupted launch leaves its partial log in `game/citadel/` (kept as
  before; documented).

## Final report

Files: `bin/cvarlist-capture` (50 lines; `pids` became `reap`, which kills;
header line 6 now "Fails past CVARLIST_TIMEOUT (180 s); on any exit kills its
own launch"), `docs/dev/game-runtime.kb/cvarlist-capture.md` ("Stuck or
interrupted launch" bullet). Interface unchanged.

Checks (6860), each followed by `tasklist.exe` (no `deadlock.exe`) and
`trash/desk/enum.ps1` (`Default` only):
- `CVARLIST_TIMEOUT=3` server: killed helper tree (2 PIDs), `ERROR(1)`,
  log moved to DIR, none left in `game/citadel/`.
- `INT` at 2 s client: helper + 2 children killed, launcher exit 130.
- `INT` at 5 s client: same, exit 130 (game seen tearing down, then gone).
- `TERM` at 2 s server: same, exit 143.
- `rm data/cvarlist/client.log; redo data/dlls.check/cvarlist`: both sides
  relaunched (the script is an input), passed: server 1765, client 2513.
shellcheck: only the pre-existing SC2329 (`onerror`, via trap).
Removed the one stray log my `INT` test left in `game/citadel/`.
