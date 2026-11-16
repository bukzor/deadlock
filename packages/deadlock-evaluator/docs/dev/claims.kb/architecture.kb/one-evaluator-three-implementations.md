---
label: EVALUATOR_IFACE
standing: agent
why:
- three-schemas-are-the-base.md
- generic-operators-know-no-game.md
---

# One evaluator type, three implementations

An evaluator is any function from Situation to Outcome. Three exist:
simulated (`engage ∘ compile`), measured (the live client), and
observed (replays indexed by situation). Every L4 operator takes an
evaluator, so calibration is `compare(simulated, measured)`, a
confounding check is `compare(simulated, observed)`, and a better
simulator is a drop-in. This single interface is the whole point of
the architecture.
