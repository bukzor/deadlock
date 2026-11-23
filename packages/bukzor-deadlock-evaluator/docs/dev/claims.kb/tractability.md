---
label: TRACTABILITY
standing: agent
ontology:
- explosion site
- tactic
- quotient
- interaction order
why:
- architecture.md
- representation.md
stale-when: an explosion site none of the four tactics cuts
---

# tractability -- reining in the explosions

The owner saw combinatorial blowups between the lines of the
architecture and asked for a methodology that handles all of them.

> [!@bukzor] cd601ea7#L126
> How do we reign that in, exactly? Is there a methodology (or a handful) that can be applied across various spots to handle everything? (If not, why not?)

This theory's answer: one principle, four tactics, and a checklist
applied at every explosion site, with a validation number demanded at
each. The sites and the tactic each takes:

| Explosion site | Source | Tactic |
|---|---|---|
| item sets, ~200 choose 12 | combinatorial | pareto prune in stat-per-soul, additive plus pairwise, local search from observed builds |
| purchase and skill order | sequential | dynamic programming over (souls, slots filled), soul-time as clock |
| hero × hero × build × build | product | factor through stats, then archetype quotient |
| 6v6 compositions | product | pairwise synergy terms only, sampled from observed comps |
| continuous fight state | continuous | graded Situation, breakpoint cells, Monte Carlo over observed entries |
| macro-state path | continuous | twenty dimensions, binned, GLM or small trees |
| Shapley attribution | 2^n | permutation sampling, or counterfactual single swaps |
| breakpoint lattice | product over targets | only the targets in the observed matchup distribution |
