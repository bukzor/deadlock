---
label: NUMPY_SIM
standing: agent
why:
- ../architecture.kb/engage-starts-trivial.md
---

# numpy for the simulator, lattice and pareto

engage, the breakpoint lattice and pareto are array computations
vectorized over batches of Situations. numpy is enough; a
just-in-time array library is a later swap if batch sizes demand it.
