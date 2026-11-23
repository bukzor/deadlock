---
label: SITUATION_GRADED
standing: agent
why:
- ../goals.kb/player-skill-dependence.md
- three-schemas-are-the-base.md
---

# Situation is the graded entry summary of a fight

A Situation is the state at which a fight begins: a required
core (participants with Builds, game time, soul totals, starting
health and resources, fight size, player skill) and optional detail
(positions, cooldowns) loaded only when the simulator can use it. It
is the simulator's initial condition and one of several views a replay
yields, and it is deliberately not the representation of a whole match
(`../representation.kb/event-log-is-ground-truth.md`). The owner's
critique that a snapshot cannot carry transitions is answered by the
representation theory's match-level views, not by enriching Situation.
