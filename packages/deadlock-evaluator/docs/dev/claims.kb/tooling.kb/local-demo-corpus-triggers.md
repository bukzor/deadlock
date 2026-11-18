---
label: LOCAL_DEMO_TRIGGERS
standing: open
why:
- public-match-demos-source.md
---

# What writes each kind of file in the install's replays directory?

`game/citadel/replays/` (a symlink to `addons/replays/`) holds three
kinds of file and three subdirectories, and the trigger for each is
unknown: `<match_id>.dem` (four, Apr to Sep 2026, 490 to 660 MB;
presumably the Watch tab), `auto-<date>-<time>-<map>-Deadlock.dem`
(39, from 2026-10-07 on; presumably every own game, but what turned it
on that day, and does it cover bot matches), and the `recent/`,
`pending_upload/`, `discarded/` subdirectories (created Oct 6 to 8;
empty now). The owner asked:

> [!@bukzor] cd601ea7 (2026-11-18)
> what exactly are the triggers for creating these various "local corpus" files

Settled by: the `citadel_*replay*` and `demo*` rows in `data/dlls/convars.tsv`
and `concommands.tsv` (the first grep finds death-replay and spectator
cvars, no obvious auto-record switch), the client's settings menu, and
watching the directory's mtimes across one played and one watched match.
