---
label: SEQUENTIAL_DP
standing: agent
why:
- one-principle-not-one-algorithm.md
- ../architecture.kb/build-is-a-sequence.md
- ../representation.kb/soul-time-is-the-clock.md
---

# Orders are planned by dynamic programming

Purchase and skill order is a sequential problem over a small state
(soul total, slots filled, levels taken). Dynamic programming or beam
search over that state, indexed by soul-time, replaces enumeration of
orderings.
