# Capturing the engine's own `cvarlist`

Observed on build 6860 (2026-11-10). Evidence: two captures made with
`bin/cvarlist-capture` (logs regenerable, not committed), the `cvarlist`
strings in `tier0.dll`, and `../probes/cvarlist_vs_store.py` run on each.

## Procedure

Per build, both sides, no clicks:

    ./bin/shell bin/cvarlist-capture server trash/cvarlist
    ./bin/shell bin/cvarlist-capture client trash/cvarlist

Each writes `trash/cvarlist/<build>-<side>.log` (the console log) and
`.cmd` (the exact command line), in about 5 s (server) or 8 s (client). The
script launches `game/bin/win64/deadlock.exe` directly from WSL (with
`-dedicated` for the server), with `-novid -condebug -con_logfile <marker>.log
"+log_flags Console -consoleonly" +cvarlist +differences +quit`, then moves
the log out of `game/citadel/`. It won't launch while any `deadlock.exe`
runs, and it fails unless the listing's closing total line is in the log.

- **Server** needs nothing: no Steam login, no map. `+cvarlist` runs once
  the host reaches `Host activate: Idle (console)`.
- **Client** needs Steam running and logged in. A direct `deadlock.exe`
  picks up the running Steam session (`CClientSteamContext init ok, logged
  on = 1`). It logs on to the GC and quits at `Host activate: Idle
  (levelload)`, before the hideout loads. Steam's launch options don't apply.
  Untested without Steam.
- **Stuck launch:** `timeout` ends only the WSL interop shim. The Windows
  process keeps running. The script then finds the `deadlock.exe` whose
  command line carries its unique log name and runs `taskkill.exe /T /F` on
  that PID, never on any other `deadlock.exe`.

## The log needs `log_flags`

`cvarlist` prints on the `Console` logging channel, and that channel is
`[ConsoleOnly]` (`log_dumpchannels`). So without the flag change, `-condebug`
/ `-con_logfile` logs everything except the listing. A dedicated server's
stdout still has it, but the client has no stdout. The
`"+log_flags Console -consoleonly"` argument must stay one argv. Split, the
`-consoleonly` would parse as a launch switch. With it, the log's listing is
identical to stdout's, line for line, once the prefix is stripped. The log is
complete at quit: the listing, then `differences`, then `Source2Shutdown`.

Log lines are UTF-8 with a BOM and CRLF. Each message's first line has a
`MM/DD HH:MM:SS [Channel] ` prefix, in local time. Continuation lines of a
multi-line message have none: the listing's two `--------------` rules and
its `N total convars/concommands` line.

## Listing format

    cvar list
    --------------
    <name> : <value> : <flags> : <help>      (format "%-80s : %-16s : %-32s : %s")
    --------------
    N total convars/concommands

Sorted by name. A wider field pushes the rest right, so split on `" : "`.

- **value:** the *current* value, `cmd` for a command. Floats print
  shortest (`0`, `12`, `0.8`). Vectors print as `1 0.5 0.25`. A `color`
  prints 3 components (`128 128 128` for default `128 128 128 255`). An
  empty string prints `0`. Defaults and bounds are not listed (`help <name>`
  prints them: `%s = %s ( default %s min %s max %s [%s] - %s`).
- **help:** the declaration's help, with `\n` and `\t` as spaces and `"` as
  `'`. Under that rule, all 2513 client entries equal a store declaration's
  help.
- **flags:** comma-separated words. The store flag each word tracks (every
  listed name printing the word has that flag):

  | printed | store flag | printed | store flag |
  |---|---|---|---|
  | `a` | `archive` | `user` | `userinfo` |
  | `rep` | `replicated` | `per_user` | `per_user` |
  | `nf` | `notify` | `prot` | `protected` |
  | `norecord` | `dontrecord` | `linked` | `linked_concommand` |
  | `server_cant_query` | `server_cannot_query` | `vconsole_fuzzy` | `vconsole_fuzzy_matching` |
  | `cheat`, `release`, `demo`, `menubar_item`, `vconsole_set_focus`, `execute_per_tick`, `server_can_execute`, `clientcmd_can_execute` | same name | | |

  `sv` and `cl` name the registering side (`server.dll`, `client.dll`). A
  name both register prints both. Never printed: `client_can_execute`,
  `commandline_enforced`, `defensive`, `execute_immediately`,
  `gameinfo_cannot_override`, `reference`, `snapshot_ignored`.

## What it lists

Server 1765 entries, client 2513. Every listed name is in
`data/dlls/{convars,concommands}.tsv`. The listing omits three classes of
declarations:

- `developmentonly`: no listed name has only `developmentonly` declarations;
- `hidden`: no listed name has a `hidden` declaration (39 unlisted on the
  client, e.g. `tv_broadcast_origin_auth`, `gameui_activate`);
- the `-` half of a `+`/`-` command pair (`-chatwheel`, `-in_ability_ping`).

Every other declaration in a loaded DLL is listed. The client leaves out
only the DLLs it didn't load: `rendersystemvulkan.dll` (it runs dx11) and
`resourcecompiler.dll`. The server also leaves out client-only DLLs and
most of `client.dll`. So `+cvarlist` runs late enough: every loaded DLL's
cvars are registered by then.

## Values are not the store's defaults

- `gameinfo.gi`'s `ConVars` block overrides defaults at startup. All 19
  server values that differ from the store's default are named there (e.g.
  `rate` 786432 vs 80000, `fps_max` 400 vs 120). `differences` measures from
  the overridden default: on the server it prints `no results`.
- The client also loads the user's archived settings. `differences` lists
  them (about 70 here, `citadel_hideout_hero_id 86`), as a `name value`
  table after the listing.

So an oracle comparing defaults must apply `gameinfo.gi` overrides or take
the server's values, and skip the client's `differences` names.
