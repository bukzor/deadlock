---
label: SEGMENTATION
standing: bare
verify: >-
  ./bin/shell sh -c 'redo-ifchange data/tools/boon data/replays/139163969.dem &&
  data/tools/boon.d/bin/python -I
  packages/bukzor-deadlock-evaluator/docs/dev/claims.kb/representation.kb/segmentation-from-events.py
  data/replays/139163969.dem'
---

# Fights segment from hero damage alone

On ranked demo 139163969, opposing-team hero damage clustered (`segmentation-from-events.py`) by boon's
`teamfights` sweep (any participant count) at a 10 s gap and 3000-unit
radius gives 90 episodes, median 13.3 s. All 74 kills fall inside one;
72 episodes (80%), with 73 kills, carry damage from both teams;
the other 18 are one-sided. A 1500 radius splits fights (56-64% two-sided); no
radius scores 88% only by merging concurrent lanes into map-wide episodes.
Checked against kills, not the minimap.

Agent judgment: rotations versus farm windows needs a trial. Positions
arrive every tick (64 Hz per hero), but jungle farming
walks camp to camp like a rotation, so separating them wants camp
geometry (`neutrals`) or a labeled replay.
