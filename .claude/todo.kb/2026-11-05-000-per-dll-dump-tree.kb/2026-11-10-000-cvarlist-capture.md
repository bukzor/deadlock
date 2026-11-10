---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - docs/dev/cvar-dump.kb/capture-approach.kb/runtime-cvarlist.md
  - docs/dev/cvar-dump.kb/validation.md
  - docs/dev/game-runtime.kb/CLAUDE.md
  - docs/dev/game-runtime.kb/local-bot-match.md
  - docs/dev/environment.kb/game-install-paths.md
---

# Capture the engine's own `cvarlist`, server and client

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the step "On-demand
check: the `cvarlist` oracle")

## Problem Statement

The oracle check (`validation.md`, "Oracle") compares the store with the
engine's own `cvarlist`, for the same build. A later unit builds the check;
it needs real captures first. This unit finds out how to get them and gets
one of each on 6860:

- **Server:** a dedicated server, e.g. `deadlock.exe -dedicated … +cvarlist
  +quit` with `-condebug -con_logfile <file>` (`local-bot-match.md` has the
  command line the client itself uses).
- **Client:** a full client launch, which needs Steam: e.g. `cmd.exe /c start
  "steam://run/1422450//<args>/"`, or `deadlock.exe` directly while Steam
  runs. The install's launch options already have `-console -condebug`
  (`console.log`).

The host has a display. A game window or console that opens and closes is
fine. Automate it from the command line as far as it goes. Settle and report:

- whether `+cvarlist` runs late enough to list every loaded DLL's cvars
  (compare the module coverage against `data/dlls/convars.tsv`);
- whether the log is complete when the process quits;
- the listing's exact format (columns, flag spelling, how help and values
  print), and whether `developmentonly` entries are omitted
  (`runtime-cvarlist.md`'s `[!QUESTION]`).

**Guardrails:**
- If Deadlock is already running, stop and report. Never kill the user's
  game.
- No matchmaking, lobby or match: launch, list, quit.
- Each launch must end within a few minutes. Kill only processes you started.
  A WSL process group (`setsid`, `kill -- -$PGID`) doesn't reach Windows
  processes. Use `taskkill.exe /T /F /PID <pid>` for a direct launch's tree.
  A Steam launch's `deadlock.exe` is Steam's child, not yours: give each
  launch a unique marker in its arguments (e.g. its `-con_logfile` name),
  and kill only the process whose command line carries it.

**If a step needs the user** (a Steam dialog, a login, a click), stop
automating at that step. Write the manual steps as
`docs/dev/game-runtime.kb/cvarlist-capture.md`: what to run, what to click,
where the log lands, and where to copy it for the check. Make it
reusable for every new build, not tied to this run. If the whole capture
automates, write that file anyway, as the procedure with its commands, and
put any reusable launcher in `bin/` (bash ≤50 lines).

**Results:** leave everything you ran and everything it produced where the
user can rerun, amend and review it.
- **Scripts:** every script you ran to launch, wait, kill or inspect becomes
  a file, not a one-off command line. The reusable launcher goes in `bin/`.
  Anything else the KB cites as evidence goes in `docs/dev/probes/`, per its
  `CLAUDE.md`.
- **Captures:** keep the logs in `trash/cvarlist/` (Valve data is not
  committed, `docs/dev/probes/CLAUDE.md`). Name each with its build and
  side, and put next to each the exact command that made it.
- **Report:** quote short excerpts.

**Scope:** `docs/dev/game-runtime.kb/cvarlist-capture.md` (new), at most one
new `bin/` script, `runtime-cvarlist.md` (resolve its `[!QUESTION]` if the
capture answers it). No `src/` code: the parser and check are the next unit.

## Steps

- [x] Preconditions: build 6860 (`steam.inf`), Deadlock not running, Steam running
- [x] Server capture: dedicated, direct `deadlock.exe` (no Steam login needed)
- [x] Client capture: direct `deadlock.exe` while Steam runs; no clicks
- [x] Settle coverage, log completeness, format, `developmentonly`
- [x] `bin/cvarlist-capture`, `cvarlist-capture.md`, `runtime-cvarlist.md`

## Decisions

- Log, not stdout, for both sides: the client has no stdout. The `Console`
  channel is `[ConsoleOnly]`, so the launch adds
  `"+log_flags Console -consoleonly"` (one argv). Log == stdout after the prefix strip.
- Direct `deadlock.exe` for the client too, not `steam://run`: no Steam
  dialog, and the launcher owns the process tree.
- Added `+differences` to each launch: it lists the client's user-changed
  values, which the oracle must skip.
- Kill by the log-name marker via `Get-CimInstance Win32_Process` and
  `taskkill /T /F`. `timeout` alone leaves the Windows process running
  (observed: `explore/6860-server-killtest.cmd`).

## Open Questions

- Client launch without Steam running: untested (would mean quitting Steam).

## Final report

Files: `bin/cvarlist-capture` (new, 50 lines, shellcheck clean),
`docs/dev/game-runtime.kb/cvarlist-capture.md` (new),
`docs/dev/probes/cvarlist_vs_store.py` (new probe; probes are outside pyright's
include), `docs/dev/cvar-dump.kb/capture-approach.kb/runtime-cvarlist.md`
(`[!QUESTION]` resolved; its old column claim was wrong).

API: `bin/cvarlist-capture server|client DIR` writes `DIR/<build>-<side>.log`
+ `.cmd`. Exit 0 only if `N total convars/concommands` is in the log. Env:
`DEADLOCK_HOME`, `CVARLIST_TIMEOUT` (180).

Captures (6860, `trash/cvarlist/`): `6860-server.log` (1765 entries, 5 s),
`6860-client.log` (2513, 8 s), each with `.cmd`, `.vs-store.txt` (the probe's
output) and `.vs-store.cmd`. Exploratory runs are in `explore/`, each with its `.cmd`.

Findings (detail in `cvarlist-capture.md`):
- Row format `%-80s : %-16s : %-32s : %s`: name, *current* value (`cmd` for
  commands), flag words, help (`\n`/`\t` printed as spaces, `"` as `'`: 2513/2513 match).
  No default or bounds.
- Flags abbreviated: `a`=archive, `rep`, `nf`=notify, `norecord`, `prot`,
  `user`=userinfo, `linked`, `server_cant_query`, `vconsole_fuzzy`. `sv`/`cl`
  = registering side. Never printed: `defensive`, `reference`,
  `gameinfo_cannot_override`, `client_can_execute`, `commandline_enforced`,
  `snapshot_ignored`, `execute_immediately`.
- Omitted: `developmentonly` (0 listed), `hidden` (0 listed, 39 unlisted),
  `-` commands. Every other declaration of a loaded DLL is listed. The only
  client gaps are unloaded `rendersystemvulkan`/`resourcecompiler`. Every
  listed name is in the store.
- Values: `gameinfo.gi` `ConVars` overrides explain all 19 server diffs from
  the store default (`rate 786432` vs `80000`). Client adds about 70 user values (`differences`).

Deviation: one probe in `docs/dev/probes/` beyond the brief's file list (the
Results section asks for cited scripts there). `llm.kb-validate` isn't
installed here. Link check: 0 broken.
