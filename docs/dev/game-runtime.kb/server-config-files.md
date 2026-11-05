# Server config files

Observed on build 6745 (2026-10-03). Strings from `citadel/bin/win64/server.dll`;
order from `citadel_local_server.log` and the client `console.log`.

On every map load the server runs "server defaults", then its config file:

- dedicated: `servercfgfile` (default `server.cfg`) — "Executing dedicated server
  config file";
- listen: `lservercfgfile` (default `listenserver.cfg`) — "Executing listen server
  config file".

Files live in `game/citadel/cfg/`; neither ships with the game. cvars are reset
to defaults only once, at process start (`ResetGameConVarsToDefaults`), so
values set by the first map's cfg persist into later ones.

Local bot match order (dedicated child): `server.cfg` on map `start` →
handoff execs `citadel_local_botmatch.cfg` + the mode cfg → changelevel to
`dl_midtown` → `server.cfg` again.

On this box `server.cfg` sets `sv_cheats 1` (see `sv-cheats.md`). Stock cfgs
are overwritten by game updates; put local changes in the non-shipped files
(`server.cfg`, `listenserver.cfg`, `autoexec.cfg`).
