---
label: MICRO_POLICY
standing: agent
why:
- engage-starts-trivial.md
- measure-is-the-ground-truth-loop.md
---

# engage's first policy is a scripted per-hero rotation

The policy input to engage (who presses what, when, at whom) has no
data source and the simulated outcomes depend on it. The first version
is a scripted per-hero rotation: deterministic, cheap, and legible when
it is wrong. What stays open is whether scripted is good enough for the
comparisons to come out right, and that is settled by calibration
against measure, not by design. If calibration fails, the next
candidates are a parameterized policy fit to replays, then a
bracket-indexed family.
