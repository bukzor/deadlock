---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - CLAUDE.md
  - ../claims.kb/tooling.kb/local-demo-corpus-triggers.md
  - ../claims.kb/tooling.kb/public-match-demos-source.md
  - ../../../../docs/dev/environment.kb/game-install-paths.md
---

# `demo triggers`: what writes each file in the install's replays dir

**Parent:** <../close-open-claims.md> (wave 4)

## Problem Statement

Goal: close, or narrow to one owner observation, the open claim
`LOCAL_DEMO_TRIGGERS`: what creates `<match_id>.dem`, `auto-*.dem`, and
the `recent/`, `pending_upload/`, `discarded/` subdirectories under
`game/citadel/replays/`, and whether `auto-*` covers bot matches. The
owner asked for the exact triggers. Evidence available without playing:

- `data/dlls/convars.tsv` and `concommands.tsv` at the repo root: every row
  whose name or help mentions replay, demo, record, upload, highlight;
  defaults, flags, and which DLL declares it.
- Client config under `game/citadel/cfg/` (`*.vcfg`, `machine_convars.vcfg`
  and kin): which of those convars the owner's client has set, and the
  files' mtimes.
- Timestamps: birth/mtime of the three subdirectories and of the first
  `auto-*.dem` (2026-10-07) against the game's patch dates (git log of the
  committed build stamp under `data/`; Steam's `appmanifest_1422450.acf`
  `LastUpdated`) and against the `botmatch*.dem` dates (Oct 3-7).
- Demo headers: with boon (`data/tools/boon.d/bin/python -I`, see
  `event-volume-per-demo.py` beside the EVENT_VOLUME claim for the
  idiom), read one `auto-*.dem` of each size class (the 0.3 MiB ones and a
  full one): map, game mode, roster size, tick rate, server address if
  present. That decides client- vs server-side and bot vs public.
- Strings in `client.dll`/`server.dll` adjacent to `pending_upload` and
  `discarded` (plain `strings | grep -C3`), naming the feature they serve.

Write what is settled into the claim body (≤120 words; cite the TSV rows
by name; keep `standing: open` if any sub-question stays unresolved,
listing exactly what the owner must observe and how). The directory
facts (which file kinds, what makes them) go into the inventory section of
`game-install-paths.md`. Read the install only; never write under it.

**Scope (only these files):**
`../claims.kb/tooling.kb/local-demo-corpus-triggers.md`,
`docs/dev/environment.kb/game-install-paths.md` (repo root, inventory
section only), `trash/unit-005/**`, this file.

## Steps

- [x] Grep the DLL TSVs; tabulate the replay/demo/record/upload rows.
- [x] Read the client cfg files; note set values and mtimes.
- [x] Collect timestamps (subdirectories, first `auto-*`, patch dates).
- [x] Read headers of three `auto-*.dem`; compare with a `botmatch*.dem`.
- [x] Grep DLL strings around the subdirectory names.
- [x] Amend the claim and the inventory; validate; commit scope + this file.

## Decisions

- Closed the claim as `standing: bare`: the local server's own log
  (`citadel_local_server.log`, last match Nov 17) prints every step --
  "Auto-Recording demo", "Replay uploading was skipped due to convar
  citadel_upload_replay_enabled", "Renamed replay ... to
  replays/discarded/replays/..." -- and the DLL strings and `cfg/server.cfg`
  back it. The `verify:` runs those greps; the log part reproduces only for
  the latest local match (the log is truncated each launch).
- The trigger is `tv_autorecord` (engine2, file pattern
  `auto-%04i%02i%02i-%02i%02i-%s-%s.dem`), not `tv_citadel_auto_record`,
  which `citadel_local_botmatch.cfg` sets to 0.
- `verify:` finds the install via `deadlock.paths.game_dir()` rather than
  the env var, which the mentions scan flags as an unresolved label.
- Retitled the claim from its question to the answer.

## Open Questions

- When `tv_enable`/`tv_autorecord` entered `cfg/server.cfg`: its mtime
  (Nov 11) postdates the first `auto-*` (Oct 7 19:20 local), and no session
  transcript wrote those lines (`claude-search tv_autorecord --all` finds
  only a Nov 5 read), so presumably a hand edit about Oct 7. Not needed for
  the trigger. No patch falls on Oct 6-7 in the build stamp's history.
- `recent/` and `pending_upload/` were created Oct 6 22:36 UTC, during the
  `botmatch3` match, a day before the first `auto-*`; what created them
  then, and what `recent/` holds after a real upload, stay inferred
  (strings only).
- The listen-server path execs `listenserver.cfg` (absent here), so it
  should record nothing; unobserved.

## Final report

Checks: `llm.kb-validate docs/dev` 79 files 0 errors; mentions 0
unresolved; grounding lists LOCAL_DEMO_TRIGGERS bare/certified; the
claim's `verify:` run and output matched.

Findings: all four file kinds answered (claim body). The inventory had two
errors, now fixed: the `auto-*` files are local bot matches, not the
owner's matchmade games, and `discarded/` is not empty -- it holds 33
finished demos (31-201 MiB) in `discarded/replays/`. All 39 `auto-*` left
in `replays/` have a zero file-info offset (unfinished; boon refuses
them); none of the 33 discarded do. Headers: `auto-*` = "SourceTV Demo",
server name "Deadlock", game dir the local install, 32 ticks/s, 1 roster
player; `botmatch*` = client recording of `127.0.0.1:<port>`; Watch-tab =
Valve srcds.

Deviations: none from scope. Scratch listings in `trash/unit-005/`.

Results live in:
`../claims.kb/tooling.kb/local-demo-corpus-triggers.md`,
`docs/dev/environment.kb/game-install-paths.md` (repo root, Local demos).
