# Local bot match hosting

Observed on build 6745 (2026-10-03). Evidence: `Local match:` strings in
`citadel/bin/win64/client.dll`, `Local bot match:` strings in `server.dll`, and
the client's `game/citadel/console.log`.

A solo bot match can run on this machine instead of a Valve server. Two client
cvars, set in `game/citadel/cfg/autoexec.cfg` on this box (`help` shows
`..._listen_server` as `[client]`, default false, no archive flag — so it
wouldn't survive a relaunch; `..._host_locally` assumed alike, unchecked):

- `citadel_bot_match_host_locally` — host the bot match locally at all. Off →
  normal matchmaking onto a Valve server.
- `citadel_bot_match_host_locally_listen_server` — "run it on our own listen
  server rather than in a dedicated server child process".

## Listen server (`..._listen_server true`)

The match runs inside the client process. If the client is already on a listen
server (the hideout is one) it reuses it — "handing the lobby to the listen
server we are already on"; otherwise it boots one first. The handoff is the
server command `citadel_start_local_bot_match <hex setup>` ("Hosts a client
provided bot match on this listen server"); the dedicated path passes the same
payload as `-citadel_local_lobby <hex>`. The hex is a protobuf:
`1` lobby_handshake_id (fixed64), `2` lobby {`3` match_mode, `4` game_mode},
`3` static_lobby {`6` members {`1` account_id, `2` persona_name, `3` team,
`5` hero_id, `6` party_index}, `9` bot_difficulty} — field names from the
server's own "armed on the listen server" log line.

**One listen-server match per client launch.** A second attempt logs
"this client has already hosted a listen server match, it has to be restarted
to host another" and then "falling back to the dedicated server path" — which
means *Valve matchmaking*, not the local child process (it sends
`k_EMsgClientToGCStartMatchmaking` immediately). Why the limit exists isn't
stated; presumably listen-server teardown isn't clean enough to reuse
(inference). There is no client-restart console command: `restart` reloads the
current map of the in-process server (in the hideout: `Loading (dl_hideout)`)
and does *not* clear the flag (refused again 53 s later, 17:39 local). `quit`,
then relaunch, e.g. from WSL `cmd.exe /c start steam://rungameid/1422450`.

Which server you're on, live: `status`. On the local dedicated server it prints
`Server:  Inactive` (this process hosts nothing) and
`Client:  Connected [127.0.0.1:27192]`, and its `steamid` matches the
`server is up. steam_id=…` line in `citadel_local_server.log`. Listen and Valve
readings not yet observed: expect `Server:` not Inactive for listen, and an
`=[A:1:…]` address for Valve.

After the fact, from `game/citadel/console.log` (rewritten each launch;
typed commands aren't logged; timestamps are local time). A listen server is
in-process, so its output is here too, prefixed `[Server]`:

- listen: `Local bot match: match is up on the listen server`
- local dedicated: `Remote Connect (127.0.0.1:<port>)`
- Valve: `falling back to the dedicated server path`, then
  `k_EMsgClientToGCStartMatchmaking`, a `match_id=`, and
  `Remote Connect (=[A:1:…])` (an SDR address)

## Dedicated child process (`..._listen_server false`)

The client spawns
`deadlock.exe -dedicated -novalveds -vconport 29002 +map start -port <port>
-condebug -con_logfile citadel_local_server.log -citadel_local_lobby <hex>
-citadel_local_report_port <report-port>`, waits up to 30 s for its ready report, then
connects to `127.0.0.1:<port>` as an ordinary remote client (port varies:
27356, 27192 seen). Its log is
`game/citadel/citadel_local_server.log`. It opens its own console window
(`citadel_bot_match_host_locally_hide_console` exists; untested).

Both paths exec `citadel_local_botmatch.cfg` on the handoff, then the
mode cfg (e.g. `citadel_botmatch_practice_6v6.cfg`) — see
`server-config-files.md`. Cheats on either path: `sv-cheats.md`.
