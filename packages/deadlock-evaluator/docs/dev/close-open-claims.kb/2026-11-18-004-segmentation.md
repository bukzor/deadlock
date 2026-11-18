---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-18-002-event-volume.md
required-reading:
  - CLAUDE.md
  - ../claims.kb/representation.kb/segmentation-from-events.md
  - ../claims.kb/representation.kb/typed-episodes.md
  - ../claims.kb/architecture.kb/situation-is-a-graded-episode-entry.md
  - ../claims.kb/tooling.kb/reuse-a-demo-parser.md
  - 2026-11-18-002-event-volume.md
---

# `segmentation`: cut one demo into fight episodes from damage events

**Parent:** <../close-open-claims.md> (wave 3)

## Problem Statement

Goal: close `SEGMENTATION` for fights. From the public demo's
(`data/replays/139163969.dem`, parsed tables already in
`trash/unit-002/139163969/` as Parquet) damage events (hero-on-hero only), cluster in time and space: a gap longer than
G seconds or farther than R units starts a new episode. Sweep G over
{5, 10, 15} and R over {1500, 3000, none} and report episode counts and
median duration per setting. Pick the setting whose boundaries agree
with kill events (every kill inside an episode; no episode without
damage from both teams) and state the agreement rate.

Use `data/tools/boon.d/bin/python -I` (it has polars and boon). Unit 002
noted boon's `game_start_tick` is None on the April demo, so stay on the
November one; its `tick_to_match_clock` works there.

Then assess rotations and farm windows: can they be told apart from
position tracks alone, at the position-update rate unit 002 measured?
Answer yes, no, or needs-a-trial with one sentence of reason.

Rewrite `segmentation-from-events.md`: fights measured (`standing:
bare`, `verify:` the script), the rest as an `agent` sentence. Script
and outputs stay in `trash/unit-004/`; if the script is worth keeping,
say so in Open Questions and the coordinator will place it.

**Scope (only these files):** `../claims.kb/representation.kb/segmentation-from-events.md`;
this file; `trash/unit-004/`.

## Steps

- [x] Segment script `trash/unit-004/segment.py`: hero-on-hero damage, G x R
  sweep, kill and two-sided agreement; cross-check against `boon.teamfights`.
- [x] Position-track probe (`trash/unit-004/position_rate.py`): update rate.
- [x] Rewrite `segmentation-from-events.md`; validate ledger.
- [x] Final report; commit scope + this file.

## Decisions

- Clustering is boon 0.19.0's own `Demo.teamfights` sweep (nearest live
  fight whose running centroid is within R, last event within G), run with
  `min_players=1`. The script re-implements its 20-line loop only because
  boon returns no per-event labels, which the two-sided check needs; every
  setting's episode count equals `demo.teamfights(...)` exactly.
- "Hero-on-hero" = boon's filter: both ids nonzero, different, opposing
  `team_num`; 14,403 of 58,845 damage rows.
- Picked G=10 s, R=3000. "Every kill inside an episode" holds at all nine
  settings (a kill tick is a damage tick), so it cannot discriminate; the
  two-sided rate rises monotonically with merging, so R=none wins it
  (88%) by producing map-wide episodes (p90 spread 12.6k units on an
  ~18k x 15k map). Among bounded radii, 10/3000 reaches 80% where 15/3000
  gains 2 points for 12 fewer, longer episodes.
- Rotations vs farm: needs-a-trial, not no: 64 Hz is ample; the obstacle
  is semantic (jungle farming traverses), not resolution.

## Open Questions

- `segment.py` is worth keeping: the claim's `verify:` points at
  `trash/unit-004/segment.py` per the brief and breaks on a trash sweep.
  Suggest placing it beside the claim as `segmentation-from-events.py`
  (unit 002's precedent) and updating `verify:`.
- `typed-episodes.md` estimates ~100 episodes per match; fights alone give
  72 two-sided (90 with pokes) here, so the total across all types is
  likely higher. Out of scope; not edited.
- The minimap-by-eye check the old claim named was not done; kills stood in.
- One demo only; the setting is not cross-validated on another public match.

## Final report

- Sweep (public demo 139163969, 14,403 hero-on-hero damage events, 74
  kills): `trash/unit-004/sweep.tsv`. Episodes / median s by G x R:
  5 s: 206/6.2, 128/8.3, 44/16.4; 10 s: 165/9.0, 90/13.3, 24/42.7;
  15 s: 152/9.3, 78/17.8, 16/65.4 (R = 1500, 3000, none).
- Chosen 10 s / 3000: kills inside an episode 74/74 (100%); episodes with
  damage from both teams 72/90 (80%); kills in those 73/74 (99%).
- Position rate: one row per hero per tick (64 Hz; 1.43M rows over 135k
  ticks, a few multi-second gaps), x/y changes on 94% of alive rows
  (`trash/unit-004/position_rate.txt`). Rotations vs farm: needs-a-trial.
- Result lives in `../claims.kb/representation.kb/segmentation-from-events.md`
  (`standing: bare`, SEGMENTATION certified by grounding). Ledger:
  `llm.kb-validate` 0 errors, `mentions` 0 findings. Runtime ~20 s.
- Deviations: added kills-in-two-sided and spread columns, since the brief's
  two criteria alone could not pick a setting.
