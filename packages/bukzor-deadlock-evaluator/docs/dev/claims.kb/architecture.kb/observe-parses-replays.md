---
label: OBSERVE
standing: agent
why:
- one-evaluator-three-implementations.md
- ../representation.kb/event-log-is-ground-truth.md
---

# observe yields situations and outcomes from replays

`observe(replay) → stream of (Situation, Outcome)` is a fold over the
replay's events. Its first version is a stub emitting a hand-written
situation distribution, so the applications run before any parser
exists. It is the source of every "on average".
