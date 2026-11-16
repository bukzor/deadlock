---
label: COMPOSITIONS
standing: agent
why:
- ../goals.kb/matchup-conditioning.md
- ../goals.kb/patch-impact.md
- one-evaluator-three-implementations.md
- generic-operators-know-no-game.md
---

# Each goal is a short composition

| Goal | Composition |
|---|---|
| skill point A vs B | `compare(aggregate(D, simulated), A, B)` |
| item A vs B | the same, with `economy` making A and B soul-equivalent at t |
| dominance | `pareto` over `compile` per soul, then over `aggregate ∘ simulated` |
| explain a popular build | `attribute(aggregate ∘ simulated, ingestedBuild)` |
| synthesize a build | `search(aggregate ∘ simulated, economy constraints)` |
| matchup build | the same, opponent slot fixed in D |
| patch impact | `compare` across two `compile` versions |
| where the meta is wrong | `compare(search(...), ingestedBuild)` then `attribute` |
| calibration | `compare(simulated, measured)` over a Situation sample |

D is the situation distribution from `observe`. No row needs a new
component; a goal that did would be the signal to revise this theory.
