# sv_cheats and the "server operator"

Observed on build 6745 (2026-10-03). Strings from `bin/win64/engine2.dll`.

`sv_cheats` is a replicated cvar: a remote client typing it gets
"Can't change replicated ConVar sv_cheats from console of client, only server
operator can change its value". There is no operator identity or admin list —
"operator" means anything issuing commands *inside the server process*:

- its console (the dedicated server's console window, or — on a listen server —
  the host's own client console; this is why `sv_cheats true` works in the
  hideout but not on a dedicated server you joined);
- a cfg it execs (`server-config-files.md`);
- VConsole attached to its `-vconport`;
- rcon: `rcon_password <pw>` on the server, then `rcon_password <pw>` and
  `rcon sv_cheats 1` on the client, gated by `rcon_connected_clients_allow`
  (untested).

With cheats off, the server rejects cheat cvars from cfgs too:
`SV: Convar 'host_timescale' is cheat protected, change ignored.` — the stock
practice-6v6 cfg hits this. Turning `sv_cheats` off reverts all FCVAR_CHEAT
cvars ("FCVAR_CHEAT cvars reverted to defaults").
