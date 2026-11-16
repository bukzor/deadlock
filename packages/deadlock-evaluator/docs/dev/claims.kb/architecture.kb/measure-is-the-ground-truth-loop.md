---
label: MEASURE
standing: agent
why:
- one-evaluator-three-implementations.md
- ../goals.kb/calibration-is-a-deliverable.md
---

# measure is the ground-truth loop

`measure(Situation) → Outcome` runs the real client: a scripted local
bot match with cheats, spawned heroes with given Builds, and damage
events logged from the console. Every other component's error is
judged against it. The parent project's game-runtime.kb already
documents the local-match hosting it needs.
