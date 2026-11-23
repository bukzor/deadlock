---
label: ENGAGE
standing: agent
why:
- micro-policy-is-the-open-input.md
- one-evaluator-three-implementations.md
- ../goals.kb/every-goal-is-a-comparison.md
---

# engage is the only home of a policy, and starts trivial

`engage(Situation, Policy) → Outcome` is the simulator and the one
component that encodes how players act. Its first version is a
closed-form Lanchester time-to-kill with no abilities
(`../representation.kb/lanchester-first-simulator.md`); it grows
toward scripted per-hero rotations. Starting crude is safe because
every goal is a comparison and common-mode error cancels. 1v1 and 2v2
cover most decisions; larger fights wait.
