# Local bot match: how the lobby is filled

Observed on build 6848 (2026-11-04). Evidence: `citadel_local_server.log`
(10:09 local), the `-citadel_local_lobby` hex on its command line, and
`Local bot match:` strings in `citadel/bin/win64/server.dll`.

On a Valve server the GC chooses the bot heroes, lanes and teams. A locally
hosted match (`local-bot-match.md`) has no GC, so the server builds the lobby
itself. It fills deterministically, which is why every local match looks alike:

- **The client sends only you**: `members { account_id, persona_name, team:
  Team0, hero_id }`, team 0 every time (`18 00` in the hex). Team0 is the Hidden
  King. Setup members without an account id are dropped ("dropping setup member
  with no account id"), so you can't add bots through the payload.
- **Bots get the lowest pickable hero_ids, in order**, skipping yours. On 6848:
  Team0 got 1,2,3,4,6 and Team1 got 7,8,10,11,12,13 (5 and 9 aren't heroes).
  The code confirms it's a sort by id, with no randomness (see below).
- **Lanes go by slot, in pairs**: slots 10–15 get lanes 1,1,4,4,6,6, and you are
  slot 10, so you're always in lane 1 (yellow).
- `match_mode` is `k_ECitadelMatchMode_PrivateLobby`. Private lobbies set lanes
  in the lobby (`citadel_private_lobby_randomize_lanes` in client.dll), which
  might be why there's no lane-swap UI; the C++ check says it isn't (see "Lane-swap code").
- `citadel_local_botmatch.cfg` (shipped) sets `citadel_pregame_wait_duration 10`
  and `citadel_pre_match_wait 10`, so the pregame is short.

## From the code (build 6851, 2026-11-05)

Disassembled with a throwaway pefile+capstone helper; RVAs are for 6851.

Client, payload builder `client.dll` 0xc954d0, called only from
`CCitadelLocalMatchHost` start 0xc94d20. The start function's arguments are
(match_mode, game_mode, bot_difficulty, hero_id, listen?). It writes exactly one
member: account id, persona name (or "Player"), hero, `team = 0`, party 0.
None of these come from a cvar. The UI caller (0x1ce6146) passes match_mode as
the literal `2`. The only cvars it reads are `..._host_locally`,
`..._listen_server`, and one more at 0x3ecc818 that picks the fallback (GC
matchmaking vs `exec citadel_botmatch_practice_6v6.cfg` + local `map`).

Server, lobby fill `server.dll` 0x775599:
- It rejects any match_mode other than 2 and forces `dl_midtown`.
- For each setup member, it requires team 0/1 and a nonzero account id, then
  copies account id, name, team, party fields and hero (if valid). `player_slot`
  is the team's base slot plus that team's member count.
- Hero pool: it walks the hero table and keeps heroes for which `0xa53d00`
  returns true. That function switches on a hero availability byte (+0xd54):
  0–2 never, 6 always, 3 only if AppID is 861490, 4–5 only if AppID is 861490
  or 3488080. Retail is 1422450, so only released heroes qualify. It then
  `qsort`s the pool with comparator 0x79ad30, which is `*a - *b`: ascending
  hero id. Next it removes the humans' heroes, gives any human without a hero
  the next pool entry, and fills Team0's free slots, then Team1's, in pool order.
- **No cvar, RNG or command line flag is read anywhere in it.** The only
  conditionals are payload validation and the AppID checks above, which let
  Valve's internal builds include in-development heroes.
- It doesn't set lanes either. They arrive later (1,1,4,4,6,6 by slot), from
  code I haven't located. There is no `{1,4,6}` int table in `.rdata`.

`citadel_start_local_bot_match <hex>` is `release client_can_execute` (DumpSource2
`commands.txt`), so a listen-server host can hand the server their own payload.
Because the server copies each member's team and hero, a hand-built payload
could put you on Team1. Members with fake account ids would take slots and the
heroes you name. Whether those slots get bots, or just sit empty, is untested.
Confirmed 2026-11-05: the last payload with `18 00`→`18 01`, typed in the
hideout, put you on the Archmother side in yellow lane. Team0 took heroes 1–7,
so your lane partner was McGinnis (8) instead of Infernus.

## Practice bots: the no-lobby path, with random heroes (build 6851)

Caller `server.dll` 0xa59106: once game state ≥3, if `citadel_spawn_practice_bots`
is on, it runs 0xa54e10. If that returns false, it runs the practice spawner
0xa54640. The spawner fills team 2, then team 3, up to `citadel_spawn_practice_bots_count`:

- When game mode (+0x130) is 6, **or** the map is `start`/`dl_midtown`, there's
  no lobby, `citadel_hero_testing_enabled` is off and `citadel_tutorial_enabled`
  is on, it first spawns the heroes named in `citadel_bot_practice_teammate`
  (team 2) and `citadel_bot_practice_opponent` (team 3). Both are
  comma-separated lists, `release`, defaults `hero_kelvin` / `hero_gigawatt`.
- Every remaining slot gets the hero `"none"`. Create-bot 0x9fc5d0 maps "none" to
  0x7f7d80, which picks `tier0!RandomInt(0, n-1)` from the available heroes.
  **So practice bots get random heroes.**

The client's own fallback (`client.dll` 0x1cb32cd) is exactly this path:
`exec citadel_botmatch_practice_6v6.cfg` + `map dl_midtown`, with no lobby.
`cfg/botmatch_random.cfg` (ours) wraps it. Tested 2026-11-05: you get team and
hero selection screens, it runs in-process (listen), and the bot heroes are random.
But Archmother got 6 bots plus you, because the count doesn't include humans. The
bots stand idle, and there's no lane-swap UI. A likely cause of the idling
(inference): with no lobby there's no bot difficulty, so no `CBotDifficultyDefinition`
behavior applies. `citadel_default_bot_difficulty` is developmentonly. Dead end
for real play.

## Fake lobby members: dead end (tested 2026-11-05)

A payload with you plus 11 fake account ids (with `citadel_bot_takeover_time 1`)
hung at "waiting on 11 other players to connect". Takeover is for players who
*disconnect*, and `citadel_bot_disconnect_takeover_enabled` (default false) is
`developmentonly`. `citadel_abandon_pregame_if_not_connected_in_s` (180, also
developmentonly) would presumably abandon a hung match eventually. Because
`player_slot` = team base + member count, and you're the only real member, you're
always slot 0 → lane 1. Commands cap at 511 chars (client.dll 0xca34bf).

`../probes/local_lobby.py` builds a single-member payload with `--team` and hero (`citadel_start_local_bot_match`).

## `citadel_create_unit`: random-hero bots inside a lobby match (untested)

Callback `server.dll` 0xa5c9a0. It requires `sv_cheats` and calls create-bot
0x9fc5d0, the practice spawner's function, so `none` gives a random hero. Team arg:
none means your team (2/3, otherwise 3); `enemy` means the other team;
`amber`/`rebel` → 2; `sapphire`/`combine` → 3; `team` → numeric index.
Tested 2026-11-05 12:41 (dedicated, `citadel_local_server.log`): one 12-line cfg
ran in pregame. Every bot came up random (tengu, haze, astro, ghost, bookworm,
shiv, dynamo, orion, werewolf, yamato, fencer) and logged "Initializing bot for
player slot N: k_ECitadelBotDifficulty_Hard", so they get the lobby difficulty.
Then the server dropped the client: "Disconnecting netchan because of excessive
CPU usage /+/ 50ms, 13, current message type: 'CNETMsg_StringCmd'"
→ NETWORK_DISCONNECT_OVERFLOW. So it's now split into
`cfg/botmatch_reroll{1,2,3}.cfg`, to exec one at a time.

Second test, 12:47 (in-game): **`bot_kick_all` is deferred.** The 3 creates in the
same batch as the kick left no `Created bot` line and no error, while the next
exec's creates worked (reusing slots 14–16). A guess: the team still counts the
kicked bots until the frame ends, so it reads as full. So reroll1 is now the kick
alone, reroll2 is 5× your team, and reroll3 is 6× enemy. One batch of 4 creates
cost "12ms to process 5 messages", well under the 50 ms limit. Only 3 of those 4
were logged; the cause is unknown. hero_deadpack (78) and hero_ratking (84)
appeared. They were released in late Oct 2026; our `heroes.json` (build 6731,
Oct 1) still says PreRelease. ratking logged missing-bone and animgraph warnings
(model path `heroes_wip/`). The pinned VRF 19.2 can't read build 6851:
"Unknown KVType for variable 'datatype': 26 (0x1A)" on `heroes.vdata_c` and
`.vcss_c`, which is why the gamedata is stuck at 6731. Still open: do they play, and which lanes do
they pick?
The handoff also execs `citadel_botmatch_practice_6v6.cfg` on the lobby server
(log line after `citadel_local_botmatch.cfg`).

## Shipped cfgs (2026-11-05 survey)

The `citadel_bot_*` *cvar names* in `citadel_botmatch_test.cfg` / `_build_test.cfg`
(`..._last_hit_threshold`, `..._free_gold_per_minute`, `..._choose_lane_on_*`,
`..._purchase_random_upgrades`, `..._spend_random_ap`, `..._use_ability_cooldown`,
`..._fight_midboss`, plus `citadel_pre_match_wait`) appear nowhere in any game
DLL, ASCII or UTF-16, even as a substring. There's also no `citadel_bot_` prefix
or format string that could build them at runtime. A first pass that used
`strings | grep -x` plus DumpSource2 couldn't have ruled out runtime-built names;
the raw byte search does.

**The settings themselves still exist**, as fields of `CBotDifficultyDefinition`
loaded from `scripts/bots/bot_difficulty.vdata`. A KV3 reader at server.dll
0x75239b reads them by name (`free_gold_per_minute`, `choose_lane_on_interval`,
`choose_balanced_lanes`, `purchase_random_upgrades`, `fight_midboss`,
`engage_last_hit_threshold`, …). Their help strings ("Fight the midboss",
"Forces bots to attack nearby enemies") sit in a 68-entry schema-description
pointer array at 0x36fdf00, next to the field-name pointers. So they're per-difficulty
data now, changeable only by editing vdata.

`citadel_bot_attack_enemies`, `_choose_balanced_lanes`, `_fight_for_idol` and
`citadel_guided_bot_match` do appear as full names, but only in a hard-coded
guided-mode override table at 0x2bf8338 (name/value pairs next to
`hero_kelvin,hero_forge`). DumpSource2 doesn't list them as cvars.
Live check, 2026-11-05: `find citadel_bot` in a listen-server console lists none
of them, guided-table names included. The registered `citadel_bot_*` set is the
`brain_*` aim/move tunables, the forced-action debug toggles (`_shoot`, `_melee`,
`_jump`, `_shop`, `_use_ability`…), the recording tools, `_practice_{teammate,opponent}`,
`_buddy`, and `citadel_bot_takeover_time` ("Time for a disconnected player to be
taken over by a bot", 30) / `_takeover_ally_range`. Live and useful:
`citadel_spawn_practice_bots[_count]`, `citadel_bot_practice_{teammate,opponent}`,
`citadel_bot_buddy` ("heroes that should follow a player around"),
`citadel_active_lane` ("0 means all", 4 in the 1v1/2v2 cfgs),
`citadel_pregame_wait_duration` (default 30, cheat), `citadel_coop_sandbox`,
`citadel_one_on_one_match`, and `citadel_allow_duplicate_heroes`.
`citadel_dev_intro_test.cfg` relies on developmentonly cvars and the `fx_test` map.

Tested by hand in-game (2026-11-05, build 6848):

- `bot_kick_all` works: it removes every bot, leaving you alone in the match.
- `citadel_bot_kick` gives "unknown command", even though server.dll contains its
  usage text ("Usage: citadel_bot_kick <bot name>..."). It's flagged
  `developmentonly` (DumpSource2 `commands.txt`, build 6848), which retail
  builds hide.
- `laneswap` gives "Unknown command 'laneswap'!" on both client and server.
  client.dll only has it as the format strings `laneswap %d` / `laneswap %d reject`,
  so the scoreboard UI probably sends it to the server as a client command,
  not a console command (inference). DumpSource2's `commands.txt` (6848) has no
  `laneswap` either, which supports this.
- `citadel_spawn_practice_bots` is a cvar flag (currently true), not a command.
- `citadel_private_lobby_randomize_lanes` is a `[client archive]` cvar, default
  false. Its `randomize_lanes` field belongs to `CSOCitadelParty.PrivateLobbySettings`,
  a party message for the GC. Confirmed 2026-11-05: setting it true leaves the
  `-citadel_local_lobby` payload byte-identical apart from the handshake id, and
  the lanes are unchanged.
- `citadel_lane_swap_available_duration -1` in `server.cfg` (which runs after the
  handoff cfgs) shows no lane-swap UI in pregame or in-game. So something other
  than the duration cvars hides it. In-game, the zipline lock explains it; pregame is unexplained;
  see "Lane-swap code".

### Lane-swap code (build 6851, 2026-11-05)

The "PrivateLobby hides it" guess above is wrong as far as C++ goes. The swap check
is the same on both sides, server 0xa24490 and client 0x791ef0 (the latter sets the
top-bar `LaneSwapAvailable` class). It requires:
- two distinct controllers on the same team (2/3);
- neither has `m_bLaneSwapLocked` (server +0x825);
- different `m_nAssignedLane` (+0x820);
- both `m_nOriginalLaneAssignment` (+0x821) nonzero;
- game state 6 `PreGameWait` with `..._duration_prematch` (-1 = always), or
  state 7 `GameInProgress` with `..._duration` (0 = never).

**Match mode isn't checked.** Panorama layout/JS (in the VPK) is unchecked.
The lock is set to 1 when you detach from the zipline (0x4b3e40, next to
`zipline_player_detached`). That's why the in-game -1 test showed nothing: by
then everyone had ridden out. The original-lane setter 0xb57450 writes both lane
fields from gamerules 0xa08550, so local matches should set the original lane.

The UI is the `LaneSwapContainer` on each teammate's top-bar portrait. Clicking
it (0x1c7f0b0) sends the client command `laneswap <n>`. The server handles it in
its ClientCommand string table (0xb2a646 → 0xb35090), next to
`selecthero`/`changeteam`/`botcmd`, so it isn't a ConCommand. That's why typing
`laneswap` fails. `cmd` ("Forward command to server") is developmentonly. If the
target is a bot (`fFlags` bit 8), the swap happens at once, with no request.
`bot_command_target <cmd>` (cheat) makes the bot under your crosshair send a
command. Its `laneswap <you>` only queues a request to you, though; a second
one cancels it. So the swap still needs your own client command.

Lane-swap cvars, from DumpSource2's `convars.txt`: `citadel_lane_swap_available_duration_prematch`
defaults to -1 and `citadel_lane_swap_available_duration` to 0 (both `cheat replicated`;
"0 to disable, -1 for infinity"). So swapping is already allowed for the whole
pregame by default, and the short pregame timer isn't what hides the UI.
`citadel_force_assigned_lane` is `developmentonly`, so it can't be used.

Still untested (strings only): `selecthero` / `clearhero` and
`citadel_allow_duplicate_heroes`.
`server.cfg` runs after the handoff cfgs (`server-config-files.md`), so it can
override what they set.
