---
label: ATTRIBUTION_DUAL
standing: agent
why:
- win-probability-added.md
- ../architecture.kb/one-evaluator-three-implementations.md
---

# Two routes to attribution, and their disagreement is signal

Counterfactual swaps in the simulator explain a gap in mechanism
terms. Shapley-style credit over win probability added in observed
data explains it in outcome terms. Both land in the same unit, so they
can be compared, and where they disagree either the simulator or the
meta is wrong. That disagreement is what `../goals.kb/where-the-meta-is-wrong.md` looks for.
