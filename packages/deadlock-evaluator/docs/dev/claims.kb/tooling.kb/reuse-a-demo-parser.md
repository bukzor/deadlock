---
label: DEMO_PARSER_REUSE
standing: agent
why:
- ../architecture.kb/observe-parses-replays.md
verify: >-
  ./bin/shell sh -c 'redo-ifchange data/tools/boon &&
  dem="$(python -m deadlock.paths citadel_dir)/botmatch1.dem" &&
  for d in player_ticks damage kills item_purchases ability_ticks;
  do data/tools/boon show "$dem" $d -n 1 --json; done'
---

# Reuse an existing Deadlock demo parser

observe wraps **boon** (github.com/pnxenopoulos/boon, PyPI
`boon-deadlock` 0.19.0, protobufs for Deadlock 6805): a Rust core, a
Python API returning Polars frames, a `boon` command. Vendored as
`data/tools/boon` (`redo data/tools/boon`: a relocatable venv, built
from the sdist on this musl host). Proven on `botmatch1.dem`; per row
it exposes:

- tick: every dataset; `Demo.tick_to_match_clock()` gives game time
- positions: `player_ticks` x/y/z per hero per tick (437k rows)
- damage: `damage` with attacker/victim hero ids, amount, ability, type (5.6k)
- item purchases: `item_purchases` (283)
- ability casts: `ability_ticks` cooldown changes (2.3k); `abilities` is empty here
- souls: `player_ticks.souls`, `gold_net_worth`

It also parses the current-patch public demo `data/replays/139163969.dem`
(build 10932) and an Apr 2026 Watch-tab demo (build 10725); there
`abilities` is populated (1.8k and 2.1k rows), so its emptiness above is
the bot demo's, not the parser's (`event-volume-per-demo.md`).

Declined: haste (unpublished, low-level, needs protoc), source2-demo
(observer boilerplate per query), demofile-net and clarity (dotnet and
Java runtimes), manta (Dota 2 only).
