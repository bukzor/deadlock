---
label: MODEL
standing: agent
ontology:
- Cycle
- Hit
- trigger
- land
- wind-up
- horizon
why:
- original-request.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
stale-when: an in-game measurement recorded in docs/dev/mechanics.kb/ disagrees
  with a timeline
---

# model -- the calls inside the damage model

Every damage source is a repeating `Cycle` of `Hit`s. A hit's
**trigger** is the player's input (trigger pull, swing, cast), its
**land** is when the damage applies, and the gap between them is the
**wind-up**: the request's bar, "left side as triggering event, right
side as actual time of damage". The **horizon** is how far a cycle is
unrolled.

The claims here are the calls made where the data is silent or
ambiguous. Each took the simple option, says so in a `note` line of the
output, and names the in-game measurement that would overturn it; that
measurement goes in `docs/dev/mechanics.kb/` at the repo root, and the
model is fixed to match. Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md), *Model*
and *Measures*.
