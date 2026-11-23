---
label: PUBLIC_DEMO_SOURCE
standing: agent
why:
- reuse-a-demo-parser.md
---

# Public match demos come from deadlock-api.com and Valve's replay host

`redo data/replays/<match_id>.dem` fetches any recent public match, no
key needed. `/v1/matches/metadata` picks the match (filters:
`match_mode` ranked/unranked, `game_mode`, `duration_s`,
`average_badge` -- tier x10 + subtier, 84 = Oracle 4; `start_time`,
mapped to a patch via `/v2/patches`, there being no patch field);
`/v1/matches/{id}/salts` yields `demo_url` on Valve's replay host.
Limits: metadata 30 req/min per address; salts 100 req/s when stored,
else a 3 req/h Steam fallback (the recipe disables it). The payload is
zstd despite its `.bz2` name: ~230 MiB for a 34-min ranked match,
353 MiB decompressed (bot demos: 71-88 MiB), served about ten days.
Match 139163969 is the first one fetched.
