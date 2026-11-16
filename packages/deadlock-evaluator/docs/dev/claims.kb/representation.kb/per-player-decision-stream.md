---
label: DECISION_STREAM
standing: agent
why:
- event-log-is-ground-truth.md
- ../goals.kb/explain-popular-builds.md
---

# Each player's decisions are a stream

Every purchase and skill point as (macro state at the time, soul total,
options available, choice). About thirty per player per match. For the
build goals this is the compact view the empirical side needs, and it
is the dataset format imitation learning uses, so it serves both
"reproduce popular" and "evaluate A vs B" without reshaping.
