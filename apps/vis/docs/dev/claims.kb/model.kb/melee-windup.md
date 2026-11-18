---
label: MELEE_WINDUP
standing: agent
why:
- ../judge-on-own-authority.md
- ../../../../../../docs/dev/decisions.kb/vis-app.md
---

# Melee wind-up is a `windup` parameter, default 0

Melee wind-up is the `timeline` query's `windup` parameter, in
seconds, defaulting to 0, and every melee timeline carries a note that
the data has no wind-up. Hero data gives melee damage and the cooldown
on hit, and no swing time. Declined: a guessed constant, which would
put an invented number in the chart with nothing marking it. At 0 the
bars have zero width and the rule at land keeps them visible.

Overturned by a frame-timed swing in-game: the measured wind-up then
becomes the default. Design:
[`vis-app.md`](../../../../../../docs/dev/decisions.kb/vis-app.md), *Model*, Melee.
