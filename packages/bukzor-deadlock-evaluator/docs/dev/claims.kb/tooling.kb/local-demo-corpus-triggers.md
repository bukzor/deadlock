---
label: LOCAL_DEMO_TRIGGERS
standing: bare
verify: >-
  ./bin/shell sh -c 'g=$(python -c "from bukzor_deadlock.paths import game_dir; print(game_dir())"); c="$g/citadel"; cat "$c/cfg/server.cfg";
  strings -n 6 "$g/bin/win64/engine2.dll" | grep -F "auto-%04i";
  strings -n 6 "$c/bin/win64/server.dll" | grep -E "^replays/|Discarding replay";
  strings -n 6 "$c/bin/win64/client.dll" | grep -F "replays/%llu.dem";
  grep -E "Auto-Recording|skipped due|Renamed replay" "$c/citadel_local_server.log"'
why:
- public-match-demos-source.md
---

# Only local bot matches write `auto-*.dem`; the Watch tab writes `<match_id>.dem`

`auto-<date>-<time>-<map>-Deadlock.dem` is the engine's `tv_autorecord` name
(`engine2.dll`, under `sv_replaysdir` = `replays`). The owner's non-shipped
`cfg/server.cfg` turns it on (`tv_enable 1`, `tv_autorecord 1`), and only a
local bot match's dedicated child execs that file, so matchmade games leave
nothing here. At post-game `CCitadelHLTVDirector` (`server.dll`) closes the
demo; `citadel_upload_replay_enabled 0`, set by `citadel_local_botmatch.cfg`,
makes it discard the file to `discarded/replays/`. A file still in `replays/`
has a zero file-info offset: its match never reached post-game.
`pending_upload/` (where an upload renames the file to `<match_id>.dem`) and
`recent/` are that director's upload paths, empty here. `<match_id>.dem` is a
client `CCitadelReplayManager` download (`replays/%llu.dem`).
