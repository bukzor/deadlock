# Game install paths

Everything hangs off one knob: `DEADLOCK_HOME`, the install root (what Steam's
"Browse local files" opens). `bukzor_deadlock.paths` derives the rest from it and
defaults to the stock native-Linux library,
`~/.local/share/Steam/steamapps/common/Deadlock`.

**On this box** the install is the *Windows* Steam copy seen through WSL, so
`DEADLOCK_HOME` is overridden in `localhost.env` (repo root, gitignored, loaded
last by `.envrc`):

    DEADLOCK_HOME="/mnt/c/Program Files (x86)/Steam/steamapps/common/Deadlock"

Do not move that path back into the code — see
`../decisions.kb/machine-local-paths-live-in-localhost-env.md`.

Layout below `$DEADLOCK_HOME`:

- **`game/`** — `bukzor_deadlock.paths.game_dir()`
  - `citadel/` — primary content mod; holds `pak01_dir.vpk` + `pak01_NNN.vpk`,
    `gameinfo.gi`, `steam.inf`, maps, etc. **This is the main target.**
  - `core/` — shared engine content (also paked).
  - `citadel_<lang>/` — localized content; **disregard non-English.**
  - `bin/win64/` — the Windows engine binaries.
  - **Logs** (in `citadel/`, timestamps in local time, typed commands not echoed):
    - `console.log` — the client console, incl. any in-process listen server
      (`[Server]` lines). Exists only because the Steam launch options here are
      `-console -condebug`; truncated at each launch.
    - `citadel_local_server.log` — the local bot match's dedicated child
      process (`-con_logfile`; see `../game-runtime.kb/local-bot-match.md`).
- **Version markers** (`citadel/steam.inf`): `ClientVersion`/`ServerVersion`
  (e.g. 6583), `SourceRevision`, `VersionDate`. Use these to label a manifest
  snapshot when diffing patches.

Other Steam paths possibly worth parsing later:
`Steam/userdata/<id>/1422450` (user data) and `Steam/appcache` (cached
match/app data).

## Local demos (inventory 2026-11-18)

Read in place; never write under the install. Sizes are on-disk MiB.

- `game/citadel/botmatch{1,3..8}.dem` -- seven local bot matches, Oct 3-7
  2026, 70-88 MiB each. Client-side recordings: no roster, 32 ticks/s.
- `game/citadel/replays/` (a symlink; `find -L`):
  - `<match_id>.dem` -- Watch-tab downloads of public matches (the client's
    replay manager), server-side, 64 ticks/s:
    `78292581` (Apr 26, 547 MiB), `81863306` (May 12, 573 MiB), `87052930`
    (Jun 6, 469 MiB), `107527112` (Sep 25, 630 MiB). Older patches.
  - `auto-YYYYMMDD-HHMM-dl_midtown-Deadlock.dem` (local start time) --
    SourceTV demos of local bot matches, written by the dedicated child
    because `cfg/server.cfg` sets `tv_enable 1` and `tv_autorecord 1`;
    server-side, 32 ticks/s, no match id. The 39 here (Oct 7 to Nov 17,
    0.3-116 MiB) are unfinished: the match never reached post-game, and the
    header's file-info offset is zero, so boon refuses them. Matchmade games
    write nothing here.
  - `discarded/replays/auto-*.dem` -- the 33 finished ones (Oct 7 to Nov 17,
    31-201 MiB): at post-game the server's replay uploader, disabled by
    `citadel_local_botmatch.cfg`, moves the demo here.
  - `pending_upload/`, `recent/` -- empty; the uploader's other paths
    (an upload renames the demo to `pending_upload/<match_id>.dem`), used
    only where upload is enabled.
- A current-patch public match lives in the repo at `data/replays/<id>.dem`
  (`redo data/replays/<match_id>.dem` fetches one; see
  `packages/bukzor-deadlock-evaluator/docs/dev/claims.kb/tooling.kb/public-match-demos-source.md`).
