---
label: BREAKPOINT_LATTICE
standing: agent
why:
- ../architecture.kb/compile-is-pure-and-emits-breakpoints.md
---

# Stat space partitions into breakpoint cells

Partition the StatVector space into cells where discrete fight outcomes
(shots to kill versus each target) are constant. Within a cell every
outcome is smooth. The cells are enumerable from compile alone, so the
worst nonlinearity becomes a finite set of regions, dominance search
becomes a lattice walk, and a breakpoint is the single most actionable
thing to tell a player.
