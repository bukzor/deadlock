---
label: VIS_SEED
standing: agent
why:
- compile-is-pure-and-emits-breakpoints.md
- engage-starts-trivial.md
- measure-is-the-ground-truth-loop.md
---

# apps/vis's damage timeline is the seed of compile and the trivial engage

`apps/vis/server/src/vis_server/timeline.py` (design:
`docs/dev/decisions.kb/vis-app.md` at the repo root, status proposed)
turns one hero's gun, melee or cast into a `Cycle` of `Hit`s from the
game data and unrolls it over a horizon; `measures.py` derives DPS and a
time to kill against a given HP, each with an in-game check string.
That is compile for one attacker and engage against a stationary
target, with the measure loop already named. The evaluator imports it
rather than re-deriving it. What it lacks and the evaluator adds: a
defender (resistances, regen), items and ability levels, a two-sided
exchange. Open: vis is its own uv workspace on Python 3.14 while this
package sits in the root workspace on 3.12, so the import edge needs
one of them moved, or the timeline lifted into the `deadlock` package.
