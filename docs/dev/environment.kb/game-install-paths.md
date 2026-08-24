# Game install paths

Everything hangs off one knob: `DEADLOCK_HOME`, the install root (what Steam's
"Browse local files" opens). `deadlock.paths` derives the rest from it and
defaults to the stock native-Linux library,
`~/.local/share/Steam/steamapps/common/Deadlock`.

**On this box** the install is the *Windows* Steam copy seen through WSL, so
`DEADLOCK_HOME` is overridden in `localhost.env` (repo root, gitignored, loaded
last by `.envrc`):

    DEADLOCK_HOME="/mnt/c/Program Files (x86)/Steam/steamapps/common/Deadlock"

Do not move that path back into the code — see
`../decisions.kb/machine-local-paths-live-in-localhost-env.md`.

Layout below `$DEADLOCK_HOME`:

- **`game/`** — `deadlock.paths.game_dir()`
  - `citadel/` — primary content mod; holds `pak01_dir.vpk` + `pak01_NNN.vpk`,
    `gameinfo.gi`, `steam.inf`, maps, etc. **This is the main target.**
  - `core/` — shared engine content (also paked).
  - `citadel_<lang>/` — localized content; **disregard non-English.**
  - `bin/win64/` — the Windows engine binaries.
- **Version markers** (`citadel/steam.inf`): `ClientVersion`/`ServerVersion`
  (e.g. 6583), `SourceRevision`, `VersionDate`. Use these to label a manifest
  snapshot when diffing patches.

Other Steam paths possibly worth parsing later:
`Steam/userdata/<id>/1422450` (user data) and `Steam/appcache` (cached
match/app data).
