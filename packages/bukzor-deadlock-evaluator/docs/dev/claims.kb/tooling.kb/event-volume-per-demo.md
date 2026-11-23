---
label: EVENT_VOLUME
standing: bare
verify: >-
  ./bin/shell sh -c 'redo-ifchange data/tools/boon data/replays/139163969.dem &&
  data/tools/boon.d/bin/python -I
  packages/bukzor-deadlock-evaluator/docs/dev/claims.kb/tooling.kb/event-volume-per-demo.py
  data/replays/139163969.dem'
---

# One public Deadlock demo holds 1.5M position and damage rows, 6M in all

Measured with boon 0.19.0 (`event-volume-per-demo.py`, 2026-11-18):

| demo | clock | ticks/s | ticks | positions | damage | purchases | casts | souls | other | all |
|---|---|---|---|---|---|---|---|---|---|---|
| botmatch1 (bot, client-side) | 25:46 | 32 | 49k | 437k | 5.6k | 283 | 2.3k | 8.4k | 267k | 713k |
| 139163969 (ranked, 2026-11-17) | 35:08 | 64 | 135k | 1,432k | 58.8k | 288 | 24.5k | 28.1k | 4,499k | 6,015k |
| 78292581 (Watch tab, 2026-04) | 41:31 | 64 | 159k | 1,738k | 70.4k | 270 | 159k | 41.5k | 5,924k | 7,892k |

positions = `player_ticks` (one row per hero per tick); casts =
`ability_ticks` + `abilities`; souls = position rows whose souls or
net worth changed; other is mostly `troopers` (4.1M on the ranked
demo) and `active_modifiers` (213k). On disk the ranked demo's tables
are 2,485 MB as JSON lines and 42.5 MB as Parquet (`polars` writes
both). Per match-minute the public demo carries 2.4x the position rows
of the bot demo (64 vs 32 ticks/s, 12 vs 11 heroes) and 7.6x the
damage rows; the bot demo is the lighter kind.
