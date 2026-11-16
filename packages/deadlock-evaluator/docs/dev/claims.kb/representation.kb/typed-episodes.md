---
label: EPISODES
standing: agent
why:
- segmentation-from-events.md
- event-log-is-ground-truth.md
- two-timescales.md
---

# A match is a sequence of typed episodes

Events cluster in space and time into episodes of a few types: fight,
farm window, rotation, objective push, respawn. Each type has an entry
summary, an exit summary and a duration; the architecture's Situation
is the fight type's entry summary. About a hundred episodes per match.
This is the semi-Markov view, and it is the bridge between the fast
and slow layers. Whether segmentation works from damage events alone
is `segmentation-from-events.md`.
