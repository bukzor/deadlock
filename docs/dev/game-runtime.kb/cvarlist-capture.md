# Capturing the engine's own `cvarlist`

Observed on build 6860 (2026-11-10). Evidence: two captures made with
`bin/cvarlist-capture` (logs regenerable, not committed), the `cvarlist`
strings in `tier0.dll`, and `../probes/cvarlist_vs_store.py` run on each.

## Procedure

Per build, both sides, no clicks:

    ./bin/shell redo data/dlls.check/cvarlist

It captures each side into `data/cvarlist/{server,client}.log` (gitignored)
and checks both against the store (`../cvar-dump.kb/validation.md`, Oracle).
A side relaunches only when one of its inputs changes (below, What a capture
reads), so a second run launches nothing. By hand, one side:

    ./bin/shell bin/cvarlist-capture server|client DIR

It writes `DIR/<build>-<side>.log` (the console log) and `.cmd` (the exact
command line), in about 5 s (server) or 8 s (client). The
script launches `game/bin/win64/deadlock.exe` from WSL on a hidden desktop
(`bin/on-hidden-desktop.ps1`, below, Focus), with `-dedicated` for the server,
and `-novid -condebug -con_logfile <marker>.log
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
- **Stuck or interrupted launch:** `timeout`, and so Ctrl-C, ends only the
  WSL interop shim. The Windows processes keep running, out of sight on the
  hidden desktop. So on every exit (success, error, timeout, `INT`, `TERM`)
  the script finds the processes whose command line carries its unique log
  name and runs `taskkill.exe /T /F` on each root among them (the helper, or
  the game once the helper is gone), never on any other process. An
  interrupted launch leaves its partial log in `game/citadel/`.

## Focus

Launched directly, either side can take the keyboard focus, intermittently:
the server's console window took the foreground in 1 of 1 launch, the client's
window in 1 of 2. Started minimized without activation (`cmd /c start /min`),
the server's console stayed back (0 of 1), but the client still took the
foreground once in 2, its window minimized: Source 2 activates its own window.
`ForegroundLockTimeout` is the default 200000 ms, and the user was active
(idle under 4 s) at every launch, so the idle rule doesn't explain it.

A window on a desktop other than the input desktop can't take the foreground,
so the script creates an unshown desktop (`CreateDesktop`) and starts the game
there (`STARTUPINFO.lpDesktop`), through `bin/on-hidden-desktop.ps1`. DX11
starts there (`Successfully created dx11 swap chain`), and each side's listing
is identical to a direct launch's. Over 4 launches, 2 per side, the foreground
never left the user's window. No flash either, by inference: nothing switches
to that desktop, and its windows are on no taskbar of the input one. Readings:
`../probes/foreground_watch.ps1`, run beside each launch. The foreground app
was always the terminal running the capture; a launch with another app in
front is untested.

## What a capture reads

Measured on the 6860 captures, matching each of the client's 58
`differences` values to the files that hold it, and hashing every candidate
file before and after one launch per side.

- **Both sides:** the DLLs and `game/citadel/gameinfo.gi`.
- **Server:** no settings file. No listed value comes from one: `server.cfg`'s
  `sv_cheats 1` lists as `false`, and `rate` keeps gameinfo.gi's 786432, not
  the 196608 in `cfg/machine_convars.vcfg`. It has no `USRLOCAL` path and fails
  to write its user config at quit.
- **Client:** the Steam account's settings under
  `<Steam>/userdata/<account>/1422450/` (its `USRLOCAL` path), not the
  install's `cfg/`. Of the 58 values, 36 are in
  `local/cfg/machine_convars.vcfg` (keys sometimes suffixed `$N`). 21 `per_user` values are in
  `remote/user_convars.vcfg` (logged `Loaded 'user_convars.vcfg' from
  SteamRemoteStorage`) and its local copies, `local/cfg/
  user_convars_0_slot0.vcfg{,_lastclouded}`. One value,
  `citadel_bot_match_host_locally`, is not archived and is set in the install's
  `cfg/autoexec.cfg` (logged `execing autoexec.cfg`). It also loads
  `local/cfg/video.txt`, which holds two listed names (`r_fullscreen_gamma`,
  `r_light_sensitivity_mode`). The install's own `cfg/machine_convars.vcfg`,
  `user_convars_0_slot0.vcfg` and `video.txt` are stale copies: they hold
  only 25 of the 58 at the listed value, 24 differ (`citadel_hideout_hero_id`
  66, listed 86) and 9 are absent.
- **A launch rewrites its inputs.** The client rewrites 12 settings files,
  three of the inputs among them (`machine_convars.vcfg` and both
  `user_convars`), and the server rewrites the install's `cfg/boot.vcfg`, all with the same
  bytes and a new mtime. Only Steam's `remotecache.vdf` changes content, and it
  is not an input.

So `data/cvarlist/<side>.log` depends on `data/dlls/file.tsv` (each DLL's
sha256), `bin/cvarlist-capture`, and `<side>.inputs`. That target is
`redo-always` and `redo-stamp`s the sha256 of each file listed above, so a
rewrite with the same bytes relaunches nothing. Assumed, not tracked: the
Steam session (login, GC state), the files `autoexec.cfg` execs, and the
Steam root lying three directories above the install, with one account
under `userdata/` that has a `1422450/`.

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
  them (58 here, `citadel_hideout_hero_id 86`) after the listing, as a
  fixed-width table under a `name` header and a rule of `_`: five columns,
  name, value, default, flags as full words (`client archive per_user`, not
  `cl, a`), help.

So an oracle comparing values must apply `gameinfo.gi` overrides and take a
`differences` name's value against its `default` column, as
`deadlock.cvarlist_check` does.
